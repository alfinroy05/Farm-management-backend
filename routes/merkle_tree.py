import hashlib

def merkle_root(hashes):
    if len(hashes) == 1:
        return hashes[0]

    new_level = []
    for i in range(0, len(hashes), 2):
        left = hashes[i]
        right = hashes[i+1] if i+1 < len(hashes) else left
        combined = left + right
        new_hash = hashlib.sha256(combined.encode()).hexdigest()
        new_level.append(new_hash)

    return merkle_root(new_level)
