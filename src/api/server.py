import io
import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from src.plc_bridge.opcua_server import VirtualIndustrialPLC
from src.pipeline import QualitySortingPipeline


plc_server = VirtualIndustrialPLC(endpoint='opc.tcp://127.0.0.1:4840/freeopcua/server/')
pipeline: Optional[QualitySortingPipeline] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipeline
    await plc_server.start()
    pipeline = QualitySortingPipeline(plc=plc_server)
    yield
    await plc_server.stop()


app = FastAPI(title='Industrial Edge Quality Sorter API', lifespan=lifespan)


class TelemetryResponse(BaseModel):
    inspected_count: int
    rejected_count: int
    pass_count: int
    defect_rate_pct: float
    line_running: bool


@app.get('/health')
async def health():
    return {'status': 'healthy', 'service': 'edge-quality-sorter'}


@app.get('/telemetry', response_model=TelemetryResponse)
async def get_telemetry():
    if not pipeline:
        raise HTTPException(status_code=503, detail='Pipeline uninitialized')
    inspected = pipeline.inspected_count
    rejected = pipeline.rejected_count
    passed = inspected - rejected
    defect_rate = (rejected / inspected * 100.0) if inspected > 0 else 0.0
    line_active = await plc_server.tag_line_running.read_value()
    return TelemetryResponse(
        inspected_count=inspected,
        rejected_count=rejected,
        pass_count=passed,
        defect_rate_pct=round(defect_rate, 2),
        line_running=line_active,
    )


@app.post('/inspect/frame')
async def inspect_uploaded_frame(file: UploadFile = File(...)):
    if not pipeline:
        raise HTTPException(status_code=503, detail='Pipeline uninitialized')
    
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if frame is None:
        raise HTTPException(status_code=400, detail='Invalid image file')
        
    result = await pipeline.process_part_frame(item_id=file.filename, frame_bgr=frame)
    return {
        'item_id': file.filename,
        'is_defective': result.is_defective,
        'defect_type': result.defect_type,
        'confidence': result.confidence,
        'latency_ms': round(result.latency_ms, 2),
    }


@app.post('/actuator/manual-pulse')
async def manual_pulse():
    await plc_server.fire_ejector_pulse(pulse_duration_s=0.05)
    return {'status': 'success', 'message': 'Ejector solenoid pulsed for 50ms'}
