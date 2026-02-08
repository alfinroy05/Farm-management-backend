import random
from datetime import datetime

def generate_reading():
    return {
        "airTemp": round(random.uniform(25, 35), 2),
        "humidity": round(random.uniform(50, 80), 2),
        "soilMoisture": round(random.uniform(25, 45), 2),
        "npk": "12-8-10",
        "soilPH": round(random.uniform(6.0, 7.0), 2),
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    readings = [generate_reading() for _ in range(6)]
    print(readings)

