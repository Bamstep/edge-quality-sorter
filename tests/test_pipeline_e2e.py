import asyncio
import pytest
import time
from src.plc_bridge.opcua_server import VirtualIndustrialPLC
from src.pipeline import QualitySortingPipeline
from src.edge_vision.detector import generate_synthetic_workpiece


@pytest.mark.asyncio
async def test_end_to_end_sorting_pipeline():
    plc = VirtualIndustrialPLC(endpoint='opc.tcp://127.0.0.1:4842/freeopcua/server/')
    await plc.start()

    try:
        pipeline = QualitySortingPipeline(
            plc=plc,
            belt_speed_mms=1000.0,
            actuator_position_mm=500.0,
        )

        t_zero = 1000.0

        # 1. Pass good part
        frame_good = generate_synthetic_workpiece(nominal_radius_px=60, with_defect=False)
        res_good = await pipeline.process_part_frame('PART_GOOD', frame_good, capture_timestamp=t_zero)
        assert res_good.is_defective is False

        # 2. Pass dimension-defective part
        frame_bad1 = generate_synthetic_workpiece(nominal_radius_px=60, with_defect=True, defect_type='dimension')
        res_bad1 = await pipeline.process_part_frame('PART_BAD1_DIM', frame_bad1, capture_timestamp=t_zero + 1.0)
        assert res_bad1.is_defective is True

        # 3. Pass surface-pitted part
        frame_bad2 = generate_synthetic_workpiece(nominal_radius_px=60, with_defect=True, defect_type='pit')
        res_bad2 = await pipeline.process_part_frame('PART_BAD2_PIT', frame_bad2, capture_timestamp=t_zero + 2.0)
        assert res_bad2.is_defective is True

        # Verify PLC telemetry registers
        val_inspected = await plc.tag_inspected.read_value()
        val_rejected = await plc.tag_rejected.read_value()
        assert val_inspected == 3
        assert val_rejected == 2

        # Verify kinematic ejection timing: 500mm / 1000mm/s = 0.5s travel delay
        # PART_BAD1 was captured at 1001.0s, so it must trigger at 1001.5s
        fired_count = await pipeline.check_and_execute_ejections(1001.5)
        assert fired_count == 1
        await asyncio.sleep(0.01)
        assert await plc.tag_ejector.read_value() is True

    finally:
        await plc.stop()
