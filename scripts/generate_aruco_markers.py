#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import cv2


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate printable ArUco navigation markers")
    parser.add_argument("--ids", nargs="+", type=int, required=True)
    parser.add_argument("--pixels", type=int, default=800)
    parser.add_argument("--output-dir", default="artifacts/aruco")
    args = parser.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

    for marker_id in args.ids:
        if not 0 <= marker_id < 50:
            raise ValueError("DICT_4X4_50 marker IDs must be between 0 and 49")
        image = cv2.aruco.generateImageMarker(dictionary, marker_id, args.pixels)
        path = out / f"aruco_4x4_50_id_{marker_id}.png"
        if not cv2.imwrite(str(path), image):
            raise RuntimeError(f"Failed to write {path}")
        print(path)


if __name__ == "__main__":
    main()
