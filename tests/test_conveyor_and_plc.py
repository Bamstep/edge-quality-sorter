import pytest
import time
import asyncio
from src.conveyor_sim.tracker import ConveyorTracker, InspectionResult
from src.plc_bridge.opcua_server import VirtualIndustrialPLC

def test_conveyor_ejection_timing():
    tracker = ConveyorTracker(belt_speed_mms=1000.0, actuator_position_mm=500.0)
    t_zero = 100.0
    bad_item = InspectionResult(
        item_id='PART_001',
        timestamp=t_zero,
        is_defective=True,
        defect_type='Surface_Pit',
        confidence=0.98,
        position_mm_at_capture=0.0,
    )

    cmd = tracker.schedule_ejection(bad_item)
    assert cmd is not None
    assert cmd.target_trigger_timestamp == pytest.approx(100.5)
    assert len(tracker.poll_actuator_triggers(current_time=100.2)) == 0

    triggers = tracker.poll_actuator_triggers(current_time=100.5)
    assert len(triggers) == 1
    assert triggers[0].item_id == 'PART_001'
    assert triggers[0].executed is True

@pytest.mark.asyncio
async def test_virtual_plc_server_variables():
    plc = VirtualIndustrialPLC(endpoint='opc.tcp://127.0.0.1:4841/freeopcua/server/')
    await plc.start()
    try:
        val = await plc.tag_line_running.read_value()
        assert val is True
        assert await plc.tag_ejector.read_value() is False
        pulse_task = asyncio.create_task(plc.fire_ejector_pulse(pulse_duration_s=0.05))
        await asyncio.sleep(0.01)
        assert await plc.tag_ejector.read_value() is True
        await pulse_task
        assert await plc.tag_ejector.read_value() is False
    finally:
        await plc.stop()
