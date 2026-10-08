import pytest
import numpy as np
from src.edge_vision.detector import EdgeVisionInspector, generate_synthetic_workpiece


def test_nominal_workpiece_passes():
    inspector = EdgeVisionInspector(nominal_radius_px=60.0)
    frame = generate_synthetic_workpiece(nominal_radius_px=60, with_defect=False)
    result = inspector.inspect_frame(frame)

    assert result.is_defective is False
    assert result.defect_type is None
    assert result.dimension_deviation_ratio <= 0.05
    assert result.latency_ms < 25.0



def test_dimension_out_of_spec_rejected():
    inspector = EdgeVisionInspector(nominal_radius_px=60.0)
    frame = generate_synthetic_workpiece(nominal_radius_px=60, with_defect=True, defect_type="dimension")
    result = inspector.inspect_frame(frame)

    assert result.is_defective is True
    assert result.defect_type == "Dimensional_Out_Of_Spec"
    assert result.dimension_deviation_ratio > 0.05


def test_surface_pitting_detected():
    inspector = EdgeVisionInspector(nominal_radius_px=60.0)
    frame = generate_synthetic_workpiece(nominal_radius_px=60, with_defect=True, defect_type="pit")
    result = inspector.inspect_frame(frame)

    assert result.is_defective is True
    assert result.defect_type == "Surface_Pitting_or_Crack"
    assert result.defect_area_px > 15.0
