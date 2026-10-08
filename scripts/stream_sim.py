import time
import random
import cv2
import requests
from src.edge_vision.detector import generate_synthetic_workpiece

API_URL = "http://localhost:8000"
print("Starting production feed simulation... (Press Ctrl+C to stop)\n")

part_index = 1000
try:
    while True:
        part_index += 1
        is_bad = random.random() < 0.25
        defect_type = random.choice(["dimension", "pit"]) if is_bad else None

        frame = generate_synthetic_workpiece(nominal_radius_px=60, with_defect=is_bad, defect_type=defect_type)
        _, buffer = cv2.imencode(".png", frame)

        status_tag = "DEFECT" if is_bad else "OK"
        filename = f"PART_{part_index}_{status_tag}.png"
        files = {"file": (filename, buffer.tobytes(), "image/png")}

        t0 = time.perf_counter()
        res = requests.post(f"{API_URL}/inspect/frame", files=files)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        if res.status_code == 200:
            data = res.json()
            verdict = "REJECT" if data["is_defective"] else "PASS"
            defect_str = f"({data['defect_type']})" if data["is_defective"] else ""
            print(f"[{verdict:<6}] Part: {filename:<22} Edge-Latency: {data['latency_ms']:5.2f}ms | Total-RTT: {elapsed_ms:5.1f}ms {defect_str}")
        else:
            print(f"Error {res.status_code}: {res.text}")

        time.sleep(0.2)

except KeyboardInterrupt:
    print("\nStopping feed. Querying final shift telemetry...")
    telem = requests.get(f"{API_URL}/telemetry").json()
    print("-" * 45)
    print(f"Total Inspected : {telem['inspected_count']}")
    print(f"Total Passed    : {telem['pass_count']}")
    print(f"Total Rejected  : {telem['rejected_count']}")
    print(f"Defect Rate     : {telem['defect_rate_pct']}%")
    print("-" * 45)