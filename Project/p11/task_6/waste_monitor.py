"""WasteMonitor: orchestrates waste detection and statistics for conveyor belt video/webcam."""

from typing import List, Optional, Tuple

import cv2
import numpy as np

import config
from waste_detector import WasteDetector, WasteDetection
from statistics import WasteStatistics


class WasteMonitor:
    def __init__(self, model_path=None, conf=None, iou=None):
        self.detector = WasteDetector(model_path=model_path, conf=conf, iou=iou)
        self.stats = WasteStatistics()
        self._frame_idx = 0

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, List[WasteDetection]]:
        self._frame_idx += 1
        detections = self.detector.detect(frame)
        self.stats.update(detections, self._frame_idx)
        annotated = self.stats.draw_annotations(frame, detections)
        annotated = self.stats.draw_hud(annotated, detections)
        return annotated, detections

    def run_on_image(self, image_path: str, output_path: Optional[str] = None) -> np.ndarray:
        frame = cv2.imread(image_path)
        if frame is None:
            raise FileNotFoundError(f"Cannot read image: {image_path}")
        annotated, detections = self.process_frame(frame)
        if output_path:
            cv2.imwrite(output_path, annotated)
            print(f"[Monitor] Saved annotated image to {output_path}")
        self._print_summary(detections)
        return annotated

    def run_on_video(self, video_source, output_path: Optional[str] = None, display: bool = True):
        cap = self._open_source(video_source)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video source: {video_source}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"[Monitor] Video: {width}x{height} @ {fps:.1f}fps")

        writer = None
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        frame_count = 0
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                annotated, detections = self.process_frame(frame)
                if writer:
                    writer.write(annotated)
                if display:
                    cv2.imshow("Waste Detection Monitor (press 'q' to quit)", annotated)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q") or key == 27:
                        break
                frame_count += 1
                if frame_count % 30 == 0:
                    cats = {}
                    for d in detections:
                        cats[d.category] = cats.get(d.category, 0) + 1
                    print(f"[Monitor] Frame {frame_count}: {len(detections)} items {dict(cats)}")
        finally:
            cap.release()
            if writer:
                writer.release()
            if display:
                cv2.destroyAllWindows()

        self.stats.print_report()

    def _open_source(self, source):
        if isinstance(source, int):
            return cv2.VideoCapture(source, cv2.CAP_DSHOW)
        return cv2.VideoCapture(source)

    def _print_summary(self, detections: List[WasteDetection]):
        total = len(detections)
        print(f"\n{'='*55}")
        print(f"  WASTE DETECTION SUMMARY")
        print(f"{'='*55}")
        print(f"  Total items detected : {total}")

        cat_counts = {}
        for d in detections:
            cat_counts[d.category] = cat_counts.get(d.category, 0) + 1

        if cat_counts:
            print(f"\n  {'Category':<12} {'Count':>6} {'Recyclable':>11}")
            print(f"  {'-'*12} {'-'*6} {'-'*11}")
            for cat in sorted(cat_counts.keys()):
                count = cat_counts[cat]
                info = config.WASTE_CATEGORIES.get(cat, {})
                rec = "Yes" if info.get("recyclable", False) else "No"
                print(f"  {cat:<12} {count:>6} {rec:>11}")
        else:
            print("\n  No waste items detected.")

        recyclable = sum(1 for d in detections if d.recyclable)
        print(f"\n  Recyclable: {recyclable} / {total} ({recyclable/total*100:.1f}%)" if total else "")
        print(f"{'='*55}\n")