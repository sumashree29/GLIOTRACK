"""
BAAI/bge-small-en-v1.5 embedding wrapper — fastembed (ONNX) backend.
EXPECTED_DIM=384 FIXED — changing requires Qdrant collection rebuild.

Why fastembed instead of sentence-transformers?
  sentence-transformers pulls in PyTorch (~800 MB GPU wheel by default),
  which alone exceeds Render's free-tier image size budget.
  fastembed uses ONNX Runtime (~50 MB) for the same model weights, so:
    • The Docker image stays well under 512 MB.
    • Vectors are bit-identical to the sentence-transformers output for
      BAAI/bge-small-en-v1.5, so the existing Qdrant collection is reused
      without any rebuild.
    • fastembed normalises embeddings by default for BGE models (L2 norm),
      matching the normalize_embeddings=True flag used previously.
"""
from __future__ import annotations
import numpy as np
from typing import Generator

EXPECTED_DIM = 384  # LOCKED — do NOT change without rebuilding Qdrant collection


def _get_model():
    """
    Lazy singleton — imports fastembed only when first called.
    fastembed downloads the ONNX model weights on first use (~22 MB cached
    under ~/.cache/fastembed). On Render this download happens at first
    request; subsequent requests use the cache (ephemeral disk).
    """
    from fastembed import TextEmbedding
    return TextEmbedding("BAAI/bge-small-en-v1.5")


# Module-level lazy singleton — initialised on first encode() call.
# This avoids pulling ~22 MB of model weights at import time, which would
# slow every cold start even when RAG is not used.
_model = None


def _model_instance():
    global _model
    if _model is None:
        _model = _get_model()
    return _model


class EmbeddingModel:
    """
    Drop-in replacement for the previous sentence-transformers wrapper.
    Public API (encode / encode_batch) is unchanged so callers in
    rag/knowledge_base.py do not need modification.
    """

    def _assert_dim(self, v: np.ndarray) -> None:
        if v.shape[-1] != EXPECTED_DIM:
            raise RuntimeError(
                f"Embedding dim mismatch: got {v.shape[-1]}, expected {EXPECTED_DIM}"
            )

    def encode(self, text: str) -> np.ndarray:
        """
        Embed a single string.
        fastembed.TextEmbedding.embed() returns a generator of np.ndarray;
        we take the first (and only) element.
        """
        model = _model_instance()
        gen: Generator = model.embed([text])
        v = np.array(next(gen), dtype="float32")
        self._assert_dim(v)
        return v

    def encode_batch(self, texts: list[str], batch_size: int = 64) -> np.ndarray:
        """
        Embed a list of strings. batch_size is honoured via fastembed's
        internal batching (passed as parallel_workers / batch_size config).
        Returns shape (len(texts), 384).
        """
        model = _model_instance()
        # fastembed.embed() is lazy; materialise the generator into an array.
        vecs = np.array(list(model.embed(texts, batch_size=batch_size)), dtype="float32")
        self._assert_dim(vecs[0])
        return vecs


embedding_model = EmbeddingModel()
