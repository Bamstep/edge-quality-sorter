import time
from dataclasses import dataclass
from typing import Tuple, Optional
import cv2
import numpy as np


@dataclass
class VisionInspectionResult:
    is_defective: bool
    defect_type: Optional[str]
    confidence: float
    defect_area_px: float
    dimension_deviation_ratio: float
    latency_ms: float


class EdgeVisionInspector:
    def __init__(
        self,
        nominal_radius_px: float = 60.0,
        dimension_tolerance: float = 0.05,
        min_defect_area_px: float = 15.0,
    ):
        self.nominal_radius_px = nominal_radius_px
        self.dimension_tolerance = dimension_tolerance
        self.min_defect_area_px = min_defect_area_px

    def inspect_frame(self, frame_bgr: np.ndarray) -> VisionInspectionResult:
        start_time = time.perf_counter()

        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return VisionInspectionResult(
                is_defective=True,
                defect_type="Missing_Part",
                confidence=1.0,
                defect_area_px=0.0,
                dimension_deviation_ratio=1.0,
                latency_ms=latency_ms,
            )

        main_contour = max(contours, key=cv2.contourArea)
        (x, y), measured_radius = cv2.minEnclosingCircle(main_contour)

        deviation_ratio = abs(measured_radius - self.nominal_radius_px) / self.nominal_radius_px
        if deviation_ratio > self.dimension_tolerance:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return VisionInspectionResult(
                is_defective=True,
                defect_type="Dimensional_Out_Of_Spec",
                confidence=float(min(1.0, 0.5 + deviation_ratio)),
                defect_area_px=0.0,
                dimension_deviation_ratio=float(deviation_ratio),
                latency_ms=latency_ms,
            )

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (19, 19))
        blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel)

        mask = np.zeros_like(gray)
        cv2.drawContours(mask, [main_contour], -1, 255, -1)
        internal_defects = cv2.bitwise_and(blackhat, blackhat, mask=mask)

        _, defect_thresh = cv2.threshold(internal_defects, 30, 255, cv2.THRESH_BINARY)
        defect_contours, _ = cv2.findContours(defect_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        total_defect_area = 0.0
        for dc in defect_contours:
            area = cv2.contourArea(dc)
            if area >= self.min_defect_area_px:
                total_defect_area += area


        latency_ms = (time.perf_counter() - start_time) * 1000.0

        if total_defect_area > 0:
            return VisionInspectionResult(
                is_defective=True,
                defect_type="Surface_Pitting_or_Crack",
                confidence=float(min(1.0, 0.7 + (total_defect_area / 500.0))),
                defect_area_px=float(total_defect_area),
                dimension_deviation_ratio=float(deviation_ratio),
                latency_ms=latency_ms,
            )

        return VisionInspectionResult(
            is_defective=False,
            defect_type=None,
            confidence=0.99,
            defect_area_px=0.0,
            dimension_deviation_ratio=float(deviation_ratio),
            latency_ms=latency_ms,
        )


def generate_synthetic_workpiece(
    nominal_radius_px: int = 60,
    with_defect: bool = False,
    defect_type: Optional[str] = None,) -> np.ndarray:
    frame = np.zeros((300, 300, 3), dtype=np.uint8)
    center = (150, 150)
    radius = nominal_radius_px
    if with_defect and defect_type == "dimension":
        radius = int(nominal_radius_px * 1.25)
    cv2.circle(frame, center, radius, (200, 200, 200), -1)
    if with_defect and defect_type == "pit":
        cv2.circle(frame, (center[0] + 15, center[1] + 10), 6, (20, 20, 20), -1)
        cv2.circle(frame, (center[0] - 12, center[1] - 8), 5, (15, 15, 15), -1)
    return frame
