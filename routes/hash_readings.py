import json
import hashlib

def hash_reading(reading: dict) -> str:
    """
    Deterministically hash a single sensor reading.
    - Stable ordering
    - No whitespace ambiguity
    - Safe for Merkle trees & blockchain verification
    """

    normalized = json.dumps(
        reading,
        sort_keys=True,
        separators=(",", ":")
    )

    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
