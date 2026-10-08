import asyncio
import time
from typing import Optional, List, Dict
from asyncua import ua
from src.conveyor_sim.tracker import ConveyorTracker, InspectionResult
from src.edge_vision.detector import EdgeVisionInspector, VisionInspectionResult
from src.plc_bridge.opcua_server import VirtualIndustrialPLC


class QualitySortingPipeline:
    def __init__(
        self,
        plc: VirtualIndustrialPLC,
        belt_speed_mms: float = 1200.0,
        actuator_position_mm: float = 500.0,
        actuator_pulse_duration_ms: float = 50.0,
    ):
        self.plc = plc
        self.tracker = ConveyorTracker(
            belt_speed_mms=belt_speed_mms,
            actuator_position_mm=actuator_position_mm,
            actuator_pulse_duration_ms=actuator_pulse_duration_ms,
        )
        self.inspector = EdgeVisionInspector()
        self.inspected_count = 0
        self.rejected_count = 0
        self.watchdog_counter = 0
        self.log_events: List[Dict] = []

    async def step_watchdog(self) -> int:
        self.watchdog_counter = (self.watchdog_counter + 1) % 65535
        await self.plc.tag_watchdog.write_value(ua.Variant(self.watchdog_counter, ua.VariantType.Int32))
        return self.watchdog_counter

    async def process_part_frame(
        self,
        item_id: str,
        frame_bgr,
        capture_timestamp: Optional[float] = None,
    ) -> VisionInspectionResult:
        t_capture = capture_timestamp if capture_timestamp is not None else time.time()

        vision_res = self.inspector.inspect_frame(frame_bgr)
        self.inspected_count += 1

        insp_record = InspectionResult(
            item_id=item_id,
            timestamp=t_capture,
            is_defective=vision_res.is_defective,
            defect_type=vision_res.defect_type,
            confidence=vision_res.confidence,
            position_mm_at_capture=0.0,
        )

        if vision_res.is_defective:
            self.rejected_count += 1
            cmd = self.tracker.schedule_ejection(insp_record)
            self.log_events.append({
                'item_id': item_id,
                'event': 'SCHEDULED_EJECTION',
                'defect': vision_res.defect_type,
                'target_time': cmd.target_trigger_timestamp if cmd else None,
            })

        # Update telemetry registers with strict Int32 types
        await self.plc.tag_inspected.write_value(ua.Variant(self.inspected_count, ua.VariantType.Int32))
        await self.plc.tag_rejected.write_value(ua.Variant(self.rejected_count, ua.VariantType.Int32))

        # Write Handshake Verdicts to PLC
        await self.plc.tag_last_inspected_id.write_value(item_id)
        await self.plc.tag_last_verdict.write_value(not vision_res.is_defective)
        defect_code = vision_res.defect_type if vision_res.defect_type else 'PASS'
        await self.plc.tag_last_defect_code.write_value(defect_code)

        # Pulse watchdog heartbeat
        await self.step_watchdog()

        return vision_res

    async def check_and_execute_ejections(self, current_time: float, tolerance_s: float = 0.010) -> int:
        due_cmds = self.tracker.poll_actuator_triggers(current_time, window_tolerance_s=tolerance_s)
        for cmd in due_cmds:
            asyncio.create_task(self.plc.fire_ejector_pulse())
            self.log_events.append({
                'item_id': cmd.item_id,
                'event': 'ACTUATOR_PULSE_FIRED',
                'fired_time': current_time,
            })
        return len(due_cmds)
