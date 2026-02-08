import json
import hashlib

def hash_reading(reading: dict) -> str:
    """
    Hash a single sensor reading deterministically
    """
    encoded = json.dumps(reading, sort_keys=True).encode()
    return hashlib.sha256(encoded).hexdigest()
