#!/usr/bin/env python3
from __future__ import annotations

import argparse

import cv2


def main() -> None:
    parser = argparse.ArgumentParser(description="List OpenCV-visible camera indices")
    parser.add_argument("--max-index", type=int, default=8)
    args = parser.parse_args()

    found = 0
    for index in range(args.max_index + 1):
        cap = cv2.VideoCapture(index)
        try:
            if not cap.isOpened():
                continue
            ok, frame = cap.read()
            if not ok or frame is None:
                continue
            h, w = frame.shape[:2]
            backend = cap.getBackendName() if hasattr(cap, "getBackendName") else "unknown"
            print(f"index={index} resolution={w}x{h} backend={backend}")
            found += 1
        finally:
            cap.release()

    if found == 0:
        raise SystemExit("No OpenCV-visible cameras found")


if __name__ == "__main__":
    main()
