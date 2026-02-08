from routes.hash_readings import hash_reading
from routes.merkle_tree import merkle_root
from routes.blockchain import store_merkle_root_on_chain
import time

BATCH_SIZE = 5
sensor_buffer = []

def add_reading_and_maybe_commit(reading):
    global sensor_buffer

    sensor_buffer.append(reading)
    print("📦 Buffer size:", len(sensor_buffer))

    if len(sensor_buffer) >= BATCH_SIZE:
        print("🔗 Batch full → generating Merkle root")

        hashes = [hash_reading(r) for r in sensor_buffer]
        root = merkle_root(hashes)

        batch_id = f"BATCH_{int(time.time())}"

        tx_hash = store_merkle_root_on_chain(batch_id, root)

        print("✅ Merkle root committed:", root)
        print("🔗 Tx hash:", tx_hash)

        sensor_buffer.clear()

        return {
            "batch_id": batch_id,
            "merkle_root": root,
            "tx_hash": tx_hash
        }

    return None
