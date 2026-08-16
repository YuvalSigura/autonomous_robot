from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import yaml


@dataclass(frozen=True)
class CameraCalibration:
    camera_matrix: np.ndarray
    dist_coeffs: np.ndarray


@dataclass(frozen=True)
class MarkerObservation:
    marker_id: int
    rvec: np.ndarray
    tvec: np.ndarray


def load_calibration(path: str | Path) -> CameraCalibration:
    with Path(path).open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    camera_matrix = np.asarray(data["camera_matrix"], dtype=np.float64)
    dist_coeffs = np.asarray(data["dist_coeffs"], dtype=np.float64)
    if camera_matrix.shape != (3, 3):
        raise ValueError("camera_matrix must be 3x3")
    return CameraCalibration(camera_matrix, dist_coeffs)


class ArucoLocalizer:
    """Detect known ArUco markers and estimate camera-to-marker pose.

    This provides a practical indoor pose reference for controlled experiments.
    It does not by itself create a global map: the marker's global pose must be
    known by the caller, or multiple markers must be placed at surveyed locations.
    """

    def __init__(
        self,
        calibration: CameraCalibration,
        marker_length_m: float,
        dictionary_id: int = cv2.aruco.DICT_4X4_50,
    ) -> None:
        self.calibration = calibration
        self.marker_length_m = float(marker_length_m)
        self.dictionary = cv2.aruco.getPredefinedDictionary(dictionary_id)
        self.detector = cv2.aruco.ArucoDetector(
            self.dictionary,
            cv2.aruco.DetectorParameters(),
        )

    def detect(self, frame: np.ndarray) -> list[MarkerObservation]:
        corners, ids, _ = self.detector.detectMarkers(frame)
        if ids is None or len(ids) == 0:
            return []

        half = self.marker_length_m / 2.0
        object_points = np.array(
            [
                [-half, half, 0.0],
                [half, half, 0.0],
                [half, -half, 0.0],
                [-half, -half, 0.0],
            ],
            dtype=np.float32,
        )

        observations: list[MarkerObservation] = []
        for marker_id, image_corners in zip(ids.flatten(), corners):
            ok, rvec, tvec = cv2.solvePnP(
                object_points,
                image_corners.reshape(4, 2).astype(np.float32),
                self.calibration.camera_matrix,
                self.calibration.dist_coeffs,
                flags=cv2.SOLVEPNP_IPPE_SQUARE,
            )
            if ok:
                observations.append(
                    MarkerObservation(int(marker_id), rvec.reshape(3), tvec.reshape(3))
                )
        return observations
