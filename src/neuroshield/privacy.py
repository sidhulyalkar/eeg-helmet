"""Fail-closed research authorization policy, not an identity or storage service.

Only synthetic events are public. For real recordings, integrate trusted
external identity, encryption, durable consent and independent audit logging.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable


@dataclass(frozen=True)
class Consent:
    subject_id: str
    granted_to: str  # authenticated principal identifier, not a display name
    purpose: str
    active: bool
    expires_at: datetime
    scope: tuple[str, ...]


def access_allowed(*, data_origin: str, principal: str | None = None,
                   subject_id: str | None = None, purpose: str | None = None,
                   modality: str | None = None, consents: tuple[Consent, ...] = (),
                   now: datetime | None = None) -> bool:
    if data_origin == "synthetic":
        return True
    if data_origin != "real" or not all((principal, subject_id, purpose, modality)):
        return False
    at = now or datetime.now(timezone.utc)
    if at.tzinfo is None:
        raise ValueError("now must include timezone")
    return any(c.active and c.expires_at.tzinfo is not None and at < c.expires_at and
               c.subject_id == subject_id and c.granted_to == principal and
               c.purpose == purpose and modality in c.scope for c in consents)


class AccessDenied(PermissionError):
    pass


def require_access(**kwargs):
    if not access_allowed(**kwargs):
        raise AccessDenied("Access denied: explicit current scope-and-purpose consent required")
