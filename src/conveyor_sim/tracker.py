import time
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class InspectionResult:
    item_id: str
    timestamp: float
    is_defective: bool
    defect_type: Optional[str]
    confidence: float
    position_mm_at_capture: float

@dataclass
class EjectionCommand:
    item_id: str
    target_trigger_timestamp: float
    actuator_id: int
    executed: bool = False

class ConveyorTracker:
    def __init__(
        self,
        belt_speed_mms: float = 1200.0,
        actuator_position_mm: float = 500.0,
        actuator_pulse_duration_ms: float = 50.0,
    ):
        self.belt_speed_mms = belt_speed_mms
        self.actuator_position_mm = actuator_position_mm
        self.actuator_pulse_duration_s = actuator_pulse_duration_ms / 1000.0
        self.scheduled_ejections: List[EjectionCommand] = []

    def schedule_ejection(self, result: InspectionResult) -> Optional[EjectionCommand]:
        if not result.is_defective:
            return None

        travel_distance_mm = self.actuator_position_mm - result.position_mm_at_capture
        travel_time_s = travel_distance_mm / self.belt_speed_mms
        target_time = result.timestamp + travel_time_s

        cmd = EjectionCommand(
            item_id=result.item_id,
            target_trigger_timestamp=target_time,
            actuator_id=1,
            executed=False,
        )
        self.scheduled_ejections.append(cmd)
        return cmd

    def poll_actuator_triggers(self, current_time: float, window_tolerance_s: float = 0.005) -> List[EjectionCommand]:
        to_fire = []
        for cmd in self.scheduled_ejections:
            if not cmd.executed and abs(current_time - cmd.target_trigger_timestamp) <= window_tolerance_s:
                cmd.executed = True
                to_fire.append(cmd)
        return to_fire
