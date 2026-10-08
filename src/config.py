import os
from pydantic import BaseModel


class SorterSettings(BaseModel):
    # Industrial OPC-UA Connection
    opc_endpoint: str = os.getenv("OPC_ENDPOINT", "opc.tcp://127.0.0.1:4840/freeopcua/server/")
    
    # Kinematics & Mechanics
    belt_speed_mms: float = float(os.getenv("BELT_SPEED_MMS", "1200.0"))
    actuator_position_mm: float = float(os.getenv("ACTUATOR_POSITION_MM", "500.0"))
    actuator_pulse_duration_ms: float = float(os.getenv("ACTUATOR_PULSE_DURATION_MS", "50.0"))
    
    # Vision Inspection Specs
    nominal_radius_px: float = float(os.getenv("NOMINAL_RADIUS_PX", "60.0"))
    dimension_tolerance: float = float(os.getenv("DIMENSION_TOLERANCE", "0.05"))
    min_defect_area_px: float = float(os.getenv("MIN_DEFECT_AREA_PX", "15.0"))
    
    # REST API & Server
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))


settings = SorterSettings()
