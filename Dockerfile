FROM python:3.11-slim
WORKDIR /app

# ── Runtime system dependencies only ──────────────────────────────────────────
# libgomp1  — OpenMP runtime required by onnxruntime (fastembed backend)
# No compiler toolchain (gcc/g++/gfortran/openblas) needed:
#   fastembed uses pre-built ONNX Runtime wheels (no C extension compilation).
#   All other packages in requirements.txt ship as pure-Python or manylinux
#   pre-built wheels, so no build tools are required.
# Dropping the compiler layer saves ~80 MB from the final image.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
  && rm -rf /var/lib/apt/lists/*

# Install Python dependencies — layer cached unless requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Fix R3 — run as non-root user; reduces container escape impact
RUN useradd -m -u 1000 appuser

# Copy source code but NOT .env (secrets injected via Render env vars)
COPY app/ ./app/
COPY rag/ ./rag/
COPY scripts/ ./scripts/

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
# Shell form so $PORT is expanded at runtime by /bin/sh.
# Render injects PORT at container start; exec form never sees it.
# Falls back to 8000 when running locally without PORT set.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
