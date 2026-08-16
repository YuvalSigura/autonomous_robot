from __future__ import annotations

from dataclasses import dataclass

import cv2


@dataclass(frozen=True)
class CameraConfig:
    device_index: int = 0
    width: int = 640
    height: int = 480
    fps: int = 30


class OpenCVCamera:
    """Small camera wrapper that works with any OpenCV-visible USB/CSI camera."""

    def __init__(self, config: CameraConfig) -> None:
        self.config = config
        self.cap: cv2.VideoCapture | None = None

    def open(self) -> None:
        cap = cv2.VideoCapture(self.config.device_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
        cap.set(cv2.CAP_PROP_FPS, self.config.fps)
        if not cap.isOpened():
            cap.release()
            raise RuntimeError(f"Could not open camera index {self.config.device_index}")
        self.cap = cap

    def read(self):
        if self.cap is None:
            raise RuntimeError("Camera is not open")
        ok, frame = self.cap.read()
        if not ok or frame is None:
            raise RuntimeError("Camera frame capture failed")
        return frame

    def close(self) -> None:
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def __enter__(self) -> "OpenCVCamera":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
