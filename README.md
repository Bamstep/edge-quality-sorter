
```markdown
# ⚡ Edge Quality Sorter — Industrial Automated Optical Inspection (AOI) & Sorting System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com)
[![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-5C3EE8.svg)](https://opencv.org/)
[![OPC-UA](https://img.shields.io/badge/OPC--UA-Industrial%20Protocol-black.svg)](https://opcfoundation.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![Tests Passing](https://img.shields.io/badge/tests-9%20passed-brightgreen.svg)]()

A sub-10 ms closed-loop edge AI vision inspection and pneumatic rejection system built for high-speed manufacturing environments. This solution decouples non-deterministic computer vision logic from real-time industrial PLC hardware execution.

---

## 📌 Table of Contents
- [Project Overview](#-project-overview)
- [System Architecture](#-system-architecture)
- [Key Features](#-key-features)
- [Project Layout](#-project-layout)
- [Quick Start Guide](#-quick-start-guide)
  - [Prerequisites](#prerequisites)
  - [Local Installation](#local-installation)
  - [Running Tests](#running-tests)
- [Running the System](#-running-the-system)
  - [1. Launching Edge API & Virtual PLC](#1-launching-edge-api--virtual-plc)
  - [2. Streaming Production Simulation](#2-streaming-production-simulation)
  - [3. Running via Docker](#3-running-via-docker)
- [Interface Contracts](#-interface-contracts)
  - [REST API Endpoints](#rest-api-endpoints)
  - [OPC-UA Register Map](#opc-ua-register-map)
- [Troubleshooting & Common Pitfalls](#-troubleshooting--common-pitfalls)
- [License](#-license)

---

## 🎯 Project Overview

In high-speed manufacturing (such as bearing lines, metal stamping, and pharmaceutical packaging), parts move at speeds of $1.0\text{--}1.5\text{ m/s}$. Standard software pipelines struggle with latency spikes, leading to missed pneumatic actuation windows.

This system solves that by implementing an **Industrial 2-Tier Architecture**:
1. **Edge Computer (Python/OpenCV/FastAPI):** Ingests frames via a Hardware Abstraction Layer (HAL), runs morphological segmentation in **under 7 ms**, decides nominal vs. defective, and maps ejection windows.
2. **Deterministic PLC Bridge (OPC-UA):** Maintains strict register handshakes, heartbeat watchdogs, and guarantees precise millisecond actuation without relying on Python for hard-realtime GPIO timing.

---

## 🏗 System Architecture


```

[ Physical World ]
## 🏗 System Architecture

```text
[ Physical Sensor / Beam Break ]
       |
       +--(Hardware TTL Trigger)--------> [ Industrial Camera ]
       |                                          |
       | (Part Arrival)                           | (Frame DMA via HAL)
       v                                          v
[ Industrial PLC Layer ]               [ Edge Vision Computer ]
  - Encoder mm Tracking                  - Otsu & Morphology (<7 ms)
  - Belt Velocity Sync                   - Dimensional Tolerance Check
  - Ejection Timing                      - Surface Crack/Pit Detection
       ^                                          |
       |                                          |
       +<---- OPC-UA Register Handshake ----------+
              - Last_Verdict_Pass
              - Last_Defect_Code
              - Edge_Watchdog_Heartbeat
       |
       v
[ Downstream Pneumatic Solenoid ]
  └── High-speed air pulse deflects defective part into reject bin.
```
    
  

---

## ✨ Key Features

- **Sub-7 ms Vision Engine:** Uses morphological black-hat operators, Otsu dynamic thresholding, and contour analysis to segment pitting, cracks, and dimensional variance.
- **Hardware Abstraction Layer (HAL):** Plug-and-play architecture (`CameraInterface`) supporting synthetic test benches or industrial GenICam/GigE camera SDKs.
- **Kinematic FIFO Tracking:** Accurately projects time-of-flight from inspection point to actuator based on distance and conveyor speed:
  $$\Delta t = \frac{\text{Distance to Solenoid}}{\text{Conveyor Velocity}}$$
- **Async OPC-UA Server:** Factory-ready node exposing typed `Int32`, `Float`, and `Boolean` variables with active watchdog heartbeat monitoring.
- **Production Stream Simulator:** Built-in tool simulating continuous workpiece arrivals with stochastic defect injection and shift telemetry reporting.

---

## 📂 Project Layout

```text
edge-quality-sorter/
├── src/
│   ├── api/
│   │   └── server.py           # FastAPI REST endpoints & SCADA telemetry
│   ├── conveyor_sim/
│   │   └── tracker.py          # Kinematic queue & solenoid trigger projection
│   ├── edge_vision/
│   │   ├── camera_hal.py       # Camera hardware abstraction interface
│   │   └── detector.py         # Sub-7 ms OpenCV defect inspection engine
│   ├── plc_bridge/
│   │   └── opcua_server.py     # Asynchronous OPC-UA industrial server
│   ├── config.py               # Central environment variable configuration
│   └── pipeline.py             # Closed-loop coordinator
├── scripts/
│   └── stream_sim.py           # Production feed simulator script
├── tests/
│   ├── test_api.py             # HTTP endpoint & manual pulse tests
│   ├── test_conveyor_and_plc.py# Queue displacement & OPC-UA node tests
│   ├── test_pipeline_e2e.py    # Complete closed-loop inspection pipeline tests
│   └── test_vision_detector.py # OpenCV precision & defect rejection tests
├── Dockerfile                  # Multi-stage container definition
├── docker-compose.yml          # Container stack configuration
├── requirements.txt            # Project dependencies
└── README.md                   # System documentation

```

---

## 🚀 Quick Start Guide

### Prerequisites

* **Python:** Version 3.11, 3.12, or 3.13
* **Git** installed on your operating system
* **Docker Desktop** *(Optional, for containerized runs)*

### Local Installation

1. **Clone the repository:**
```bash
git clone [https://github.com/Bamstep/edge-quality-sorter.git](https://github.com/Bamstep/edge-quality-sorter.git)
cd edge-quality-sorter

```


2. **Create and activate a virtual environment:**
* **Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1

```


* **Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate

```




3. **Install dependencies:**
```bash
pip install -r requirements.txt

```



### Running Tests

Execute the full regression test suite (9 integration, unit, and vision tests):

```bash
pytest tests/ -v

```

Expected output:

```text
======================= test session starts =======================
tests/test_api.py::test_api_health_and_telemetry PASSED      [ 11%]
tests/test_api.py::test_api_inspect_frame_upload PASSED      [ 22%]
tests/test_api.py::test_api_manual_pulse PASSED              [ 33%]
tests/test_conveyor_and_plc.py::test_conveyor_ejection_timing PASSED [ 44%]
tests/test_conveyor_and_plc.py::test_virtual_plc_server_variables PASSED [ 55%]
tests/test_pipeline_e2e.py::test_end_to_end_sorting_pipeline PASSED [ 66%]
tests/test_vision_detector.py::test_nominal_workpiece_passes PASSED [ 77%]
tests/test_vision_detector.py::test_dimension_out_of_spec_rejected PASSED [ 88%]
tests/test_vision_detector.py::test_surface_pitting_detected PASSED [100%]
======================= 9 passed in 13.5s =========================

```

---

## 🖥 Running the System

Testing the live pipeline requires two terminals (or background processes):

### 1. Launching Edge API & Virtual PLC

In **Terminal 1**, start the central edge process:

```bash
uvicorn src.api.server:app --host 0.0.0.0 --port 8000

```

This initializes:

* **FastAPI HTTP Server** at `http://localhost:8000`
* **Interactive Swagger Docs** at `http://localhost:8000/docs`
* **OPC-UA Server** at `opc.tcp://127.0.0.1:4840/freeopcua/server/`

### 2. Streaming Production Simulation

In **Terminal 2**, run the production feed simulator:

```bash
python -m scripts.stream_sim

```

You will see real-time output showing sub-7 ms edge latency decisions:

```text
Starting production feed simulation... (Press Ctrl+C to stop)

[PASS  ] Part: PART_1001_OK.png       Edge-Latency:  6.78ms | Total-RTT: 2087.1ms
[REJECT] Part: PART_1002_DEFECT.png   Edge-Latency:  6.85ms | Total-RTT: 2064.1ms (Surface_Pitting_or_Crack)
[REJECT] Part: PART_1003_DEFECT.png   Edge-Latency:  1.24ms | Total-RTT: 2072.7ms (Dimensional_Out_Of_Spec)
[PASS  ] Part: PART_1004_OK.png       Edge-Latency:  6.60ms | Total-RTT: 2071.8ms

```

Press **`Ctrl + C`** at any time to generate the end-of-shift telemetry report:

```text
---------------------------------------------
Total Inspected : 20
Total Passed    : 14
Total Rejected  : 6
Defect Rate     : 30.0%
---------------------------------------------

```

### 3. Running via Docker

If you have Docker Desktop running:

```bash
docker compose build
docker compose up -d

```

Check health:

```bash
curl http://localhost:8000/health

```

---

## 📡 Interface Contracts

### REST API Endpoints

| Method | Endpoint | Description | Sample Response |
| --- | --- | --- | --- |
| `GET` | `/health` | Service and PLC health status | `{"status":"ok","plc_connected":true}` |
| `GET` | `/telemetry` | Live shift yield, pass/reject counts | `{"inspected_count":120,"defect_rate_pct":5.2}` |
| `POST` | `/inspect/frame` | Upload multipart frame for AOI evaluation | `{"part_id":"PART_1","is_defective":false,"latency_ms":6.2}` |
| `POST` | `/actuator/manual-pulse` | Manual override to test pneumatic ejector | `{"pulse_acknowledged":true}` |

### OPC-UA Register Map

| Tag Identifier | Data Type | Access | Description |
| --- | --- | --- | --- |
| `Line_Running` | `Boolean` | Read / Write | Conveyor line operational status |
| `Belt_Speed_MM_S` | `Float` | Read | Belt velocity ($1200.0\text{ mm/s}$ default) |
| `Total_Inspected_Count` | `Int32` | Read / Write | Total parts processed |
| `Total_Rejected_Count` | `Int32` | Read / Write | Total parts rejected |
| `Edge_Watchdog_Heartbeat` | `Int32` | Read / Write | Rolling integer counter ($0\text{--}65535$) |
| `Last_Inspected_ID` | `String` | Read / Write | Part identifier tag |
| `Last_Verdict_Pass` | `Boolean` | Read / Write | `True` if nominal, `False` if defective |
| `Last_Defect_Code` | `String` | Read / Write | Reason (`NONE`, `Surface_Pitting_or_Crack`, etc.) |
| `Ejector_Solenoid_Active` | `Boolean` | Read / Write | Downstream pneumatic solenoid state |

---

## 🛠 Troubleshooting & Common Pitfalls

### 1. `ConnectionRefusedError: [WinError 10061]`

* **Cause:** Running `python -m scripts.stream_sim` before starting the server.
* **Fix:** Keep `uvicorn src.api.server:app --port 8000` running in Terminal 1, and execute the simulator in Terminal 2.

### 2. `ModuleNotFoundError: No module named 'src'`

* **Cause:** Running `python scripts/stream_sim.py` directly from subdirectories changes Python's import search path.
* **Fix:** Run the script as a module from the root directory:
```bash
python -m scripts.stream_sim

```



### 3. `failed to connect to the docker API at npipe`

* **Cause:** Docker Desktop is stopped or not running on Windows.
* **Fix:** Start Docker Desktop and wait until the whale icon turns green, or run directly on the host using `uvicorn`.

### 4. PowerShell Multiline Paste Crashing (`PSReadLine`)

* **Cause:** Terminal buffer offset errors in Windows PowerShell console during rapid multiline pasting.
* **Fix:** Temporarily disable the module in that session:
```powershell
Remove-Module PSReadLine -ErrorAction SilentlyContinue

```



---

## 📜 License

Distributed under the **MIT License**. See `LICENSE` for more information.

```

---

<FollowUp label="Want to add a GitHub Actions CI workflow to run tests automatically on push?" query="Add a GitHub Actions workflow file (.github/workflows/ci.yml) to automatically run pytest on push and pull requests."/>

```
