import hashlib
import hmac
import os


def anonymize_rut(rut: str) -> str:
    """Deterministic anon_id from a Chilean RUT via HMAC-SHA256.

    Same RUT → same anon_id, but the RUT itself is never stored.
    Strips formatting (dots, dashes) and uppercases the verifier digit ('K')
    so '19.523.183-4' and '195231834' produce the same id.
    """
    secret = os.environ.get("HMAC_SECRET", "").encode()
    if not secret:
        raise RuntimeError("HMAC_SECRET environment variable is not set")
    rut_clean = rut.replace(".", "").replace("-", "").upper().encode()
    return hmac.new(secret, rut_clean, hashlib.sha256).hexdigest()[:12]


_ANIMALS = [
    "Cóndor",
    "Puma",
    "Huemul",
    "Pudú",
    "Vizcacha",
    "Loica",
    "Chinchilla",
    "Quetru",
    "Tagua",
    "Quirquincho",
]


def generate_avatar_name(anon_id: str) -> str:
    """Render a stable display name like 'Cóndor 4521' from an anon_id.

    Uses the first hex chars of the anon_id, so the avatar is stable across
    re-ingests of the same person.
    """
    idx = int(anon_id[:2], 16) % len(_ANIMALS)
    number = int(anon_id[2:6], 16) % 9000 + 1000
    return f"{_ANIMALS[idx]} {number}"
