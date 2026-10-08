import time
from abc import ABC, abstractmethod
from typing import Optional, Callable
import numpy as np
from src.edge_vision.detector import generate_synthetic_workpiece


class CameraInterface(ABC):
    @abstractmethod
    def connect(self) -> bool:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass

    @abstractmethod
    def capture_frame(self) -> Optional[np.ndarray]:
        pass

    @abstractmethod
    def start_hardware_trigger_mode(self, callback: Callable[[np.ndarray, float], None]) -> None:
        pass


class SyntheticIndustrialCamera(CameraInterface):
    """Simulated GenICam camera supporting software trigger and synthetic defects."""
    def __init__(self, fps: float = 30.0):
        self.fps = fps
        self.is_connected = False
        self._running = False

    def connect(self) -> bool:
        self.is_connected = True
        return True

    def disconnect(self) -> None:
        self.is_connected = False
        self._running = False

    def capture_frame(self, defect_type: Optional[str] = None) -> np.ndarray:
        if not self.is_connected:
            raise RuntimeError('Camera must be connected before capturing frames.')
        has_defect = defect_type is not None
        return generate_synthetic_workpiece(nominal_radius_px=60, with_defect=has_defect, defect_type=defect_type)

    def start_hardware_trigger_mode(self, callback: Callable[[np.ndarray, float], None]) -> None:
        self._running = True
