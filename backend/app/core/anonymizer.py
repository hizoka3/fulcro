import hashlib
import hmac
import os


def anonymize_identity(name: str, rut: str) -> str:
    """Deterministic anon_id from (name, RUT) via HMAC-SHA256.

    Same name+RUT → same anon_id, but neither field is stored.
    Normalizes formatting (dots/dashes in RUT, casing and whitespace in
    name) so reasonable parser variations still collide on the same id.
    """
    secret = os.environ.get("HMAC_SECRET", "").encode()
    if not secret:
        raise RuntimeError("HMAC_SECRET environment variable is not set")
    rut_clean = rut.replace(".", "").replace("-", "").upper()
    name_clean = " ".join(name.upper().split())
    payload = f"{name_clean}|{rut_clean}".encode()
    return hmac.new(secret, payload, hashlib.sha256).hexdigest()[:12]


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
