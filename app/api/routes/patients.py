"""
Patients routes.
Fix #9  — queries were scoped to the logged-in doctor's email.
Fix #10 — rate limiter applied.
Fix #19 — audit logging on patient view.
Fix Q3  — patient_id validated: alphanumeric + hyphens/underscores only,
           max 64 chars. Prevents path traversal in R2 keys and injection.

Auth removed from GET endpoints (2026-07-06): GlioTrack is now public-read.
GET /patients, GET /patients/{id}, GET /patients/{id}/scans return all data
without requiring a JWT. POST write endpoints (create, archive, restore) are
blocked by UPLOADS_PAUSED=true — their auth is irrelevant but left in place
so the code compiles and the routes remain disabled cleanly.
"""
import re
from fastapi import APIRouter, Depends, HTTPException, Request
from app.core.auth import get_current_user
from app.database.crud import (
    get_or_create_patient, get_scans_for_patient,
    get_all_patients, get_all_archived_patients,
    get_patient_by_id_unscoped,
)
from app.services.audit import log_action
from app.core.rate_limit import api_limiter, get_client_ip
from pydantic import BaseModel

router = APIRouter(prefix="/patients", tags=["patients"])

_PATIENT_ID_RE = re.compile(r'^[A-Za-z0-9_-]{1,64}$')


def _validate_patient_id(patient_id: str):
    if not _PATIENT_ID_RE.match(patient_id):
        raise HTTPException(
            400,
            "patient_id must be 1-64 characters: letters, digits, hyphens and underscores only."
        )


class PatientIn(BaseModel):
    patient_id: str


# ── Read-only endpoints (no auth required) ────────────────────────────────────

@router.get("")
def list_patients(request: Request):
    """Return all active patients (public read)."""
    api_limiter.check(get_client_ip(request))
    patients = get_all_patients()
    log_action("anonymous", "PATIENTS_LISTED", "patient", "all", get_client_ip(request))
    return patients


@router.get("/archived")
def list_archived_patients(request: Request):
    """Return all archived patients (public read)."""
    api_limiter.check(get_client_ip(request))
    patients = get_all_archived_patients()
    return patients


@router.get("/{patient_id}/scans")
def list_scans(patient_id: str, request: Request):
    api_limiter.check(get_client_ip(request))
    _validate_patient_id(patient_id)
    # doctor_email="" → unscoped: returns all scans for this patient
    scans = get_scans_for_patient(patient_id, doctor_email="")
    log_action("anonymous", "PATIENT_SCANS_VIEWED", "patient", patient_id, get_client_ip(request))
    return scans


@router.get("/{patient_id}")
def get_patient(patient_id: str, request: Request):
    """Return a single patient record (public read)."""
    api_limiter.check(get_client_ip(request))
    _validate_patient_id(patient_id)
    patient = get_patient_by_id_unscoped(patient_id)
    if not patient:
        raise HTTPException(404, "Patient not found")
    log_action("anonymous", "PATIENT_VIEWED", "patient", patient_id, get_client_ip(request))
    return patient


# ── Write endpoints (blocked by UPLOADS_PAUSED; auth kept but irrelevant) ─────

@router.post("", status_code=201)
def create_patient(body: PatientIn, request: Request, user=Depends(get_current_user)):
    api_limiter.check(get_client_ip(request))
    _validate_patient_id(body.patient_id)
    patient = get_or_create_patient(body.patient_id, doctor_email=user["sub"])
    log_action(user["sub"], "PATIENT_CREATED", "patient", body.patient_id, get_client_ip(request))
    return patient


@router.post("/{patient_id}/archive")
def archive_patient_route(
    patient_id: str,
    request: Request,
    user=Depends(get_current_user)
):
    """Hide a patient from the active list (soft delete)."""
    api_limiter.check(get_client_ip(request))
    _validate_patient_id(patient_id)
    from app.database.crud import archive_patient
    success = archive_patient(patient_id, doctor_email=user["sub"])
    if not success:
        raise HTTPException(404, "Patient not found or not authorised")
    log_action(
        user["sub"], "PATIENT_ARCHIVED", "patient",
        patient_id, get_client_ip(request)
    )
    return {"message": f"Patient {patient_id} archived successfully"}


@router.post("/{patient_id}/restore")
def restore_patient_route(
    patient_id: str,
    request: Request,
    user=Depends(get_current_user)
):
    """Restore a previously archived patient."""
    api_limiter.check(get_client_ip(request))
    _validate_patient_id(patient_id)
    from app.database.crud import restore_patient
    success = restore_patient(patient_id, doctor_email=user["sub"])
    if not success:
        raise HTTPException(404, "Patient not found or not authorised")
    log_action(
        user["sub"], "PATIENT_RESTORED", "patient",
        patient_id, get_client_ip(request)
    )
    return {"message": f"Patient {patient_id} restored successfully"}