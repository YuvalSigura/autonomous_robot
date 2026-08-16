#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np
import yaml


def main() -> None:
    parser = argparse.ArgumentParser(description="Interactive chessboard camera calibration")
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--cols", type=int, default=9, help="Inner chessboard corners horizontally")
    parser.add_argument("--rows", type=int, default=6, help="Inner chessboard corners vertically")
    parser.add_argument("--square-mm", type=float, default=25.0)
    parser.add_argument("--samples", type=int, default=20)
    parser.add_argument("--output", default="config/camera_calibration.yaml")
    args = parser.parse_args()

    pattern_size = (args.cols, args.rows)
    square_m = args.square_mm / 1000.0
    object_template = np.zeros((args.rows * args.cols, 3), np.float32)
    object_template[:, :2] = np.mgrid[0:args.cols, 0:args.rows].T.reshape(-1, 2)
    object_template *= square_m

    object_points: list[np.ndarray] = []
    image_points: list[np.ndarray] = []

    cap = cv2.VideoCapture(args.device)
    if not cap.isOpened():
        raise SystemExit(f"Could not open camera index {args.device}")

    image_size = None
    print("Show the chessboard from varied angles/distances. SPACE=capture, Q=finish/quit.")
    try:
        while len(object_points) < args.samples:
            ok, frame = cap.read()
            if not ok or frame is None:
                raise RuntimeError("Camera frame capture failed")
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            image_size = (gray.shape[1], gray.shape[0])
            found, corners = cv2.findChessboardCorners(gray, pattern_size)

            display = frame.copy()
            if found:
                criteria = (
                    cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
                    30,
                    0.001,
                )
                refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
                cv2.drawChessboardCorners(display, pattern_size, refined, True)
            else:
                refined = None

            cv2.putText(
                display,
                f"samples {len(object_points)}/{args.samples} | SPACE capture | Q finish",
                (15, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2,
            )
            cv2.imshow("SpectraRover camera calibration", display)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            if key == ord(" ") and found and refined is not None:
                object_points.append(object_template.copy())
                image_points.append(refined)
                print(f"captured {len(object_points)}/{args.samples}")
    finally:
        cap.release()
        cv2.destroyAllWindows()

    if len(object_points) < 8:
        raise SystemExit("Need at least 8 good calibration views")
    assert image_size is not None

    rms, camera_matrix, dist_coeffs, _, _ = cv2.calibrateCamera(
        object_points, image_points, image_size, None, None
    )
    payload = {
        "rms_reprojection_error": float(rms),
        "image_size": {"width": image_size[0], "height": image_size[1]},
        "camera_matrix": camera_matrix.tolist(),
        "dist_coeffs": dist_coeffs.reshape(-1).tolist(),
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    print(f"saved {output} (RMS error={rms:.4f})")


if __name__ == "__main__":
    main()
