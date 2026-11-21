"""SafetyMonitor: orchestrates PPE detection and alert generation for video/webcam streams."""


from typing import List, Optional, Tuple

import cv2
import numpy as np

import config
from ppe_detector import PPEDetector, WorkerStatus
from alert_system import AlertSystem


class SafetyMonitor:
    def __init__(self, model_path=None, conf=None, iou=None):
        self.detector = PPEDetector(model_path=model_path, conf=conf, iou=iou)
        self.alerts = AlertSystem()
        self._frame_idx = 0

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, List[WorkerStatus], List[str]]:
        self._frame_idx += 1
        workers = self.detector.analyze(frame)
        all_alerts = []
        for worker in workers:
            triggered = self.alerts.trigger(worker, self._frame_idx)
            all_alerts.extend(triggered)
        annotated = self.alerts.annotate(frame, workers)
        return annotated, workers, all_alerts

    def run_on_image(self, image_path: str, output_path: Optional[str] = None) -> np.ndarray:
        frame = cv2.imread(image_path)
        if frame is None:
            raise FileNotFoundError(f"Cannot read image: {image_path}")
        annotated, workers, alerts = self.process_frame(frame)
        if output_path:
            cv2.imwrite(output_path, annotated)
            print(f"[Monitor] Saved annotated image to {output_path}")
        self._print_summary(workers, alerts)
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
                annotated, workers, alerts = self.process_frame(frame)
                if writer:
                    writer.write(annotated)
                if display:
                    cv2.imshow("Construction Safety Monitor (press 'q' to quit)", annotated)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q") or key == 27:
                        break
                frame_count += 1
                if frame_count % 30 == 0:
                    violators = sum(1 for w in workers if not w.is_compliant)
                    print(f"[Monitor] Frame {frame_count}: {len(workers)} workers, {violators} violations")
        finally:
            cap.release()
            if writer:
                writer.release()
            if display:
                cv2.destroyAllWindows()

        print(f"[Monitor] Processed {frame_count} frames. Stats: {self.alerts.stats}")

    def _open_source(self, source):
        if isinstance(source, int):
            return cv2.VideoCapture(source, cv2.CAP_DSHOW)
        return cv2.VideoCapture(source)

    @staticmethod
    def _print_summary(workers: List[WorkerStatus], alerts: List[str]):
        total = len(workers)
        compliant = sum(1 for w in workers if w.is_compliant)
        violators = total - compliant
        print(f"\n{'='*50}")
        print(f"  SAFETY MONITORING SUMMARY")
        print(f"{'='*50}")
        print(f"  Total workers detected : {total}")
        print(f"  Compliant workers     : {compliant}")
        print(f"  Non-compliant workers : {violators}")
        print(f"  Alerts triggered      : {len(alerts)}")
        if violators > 0:
            print(f"\n  VIOLATIONS:")
            for i, w in enumerate(workers):
                if not w.is_compliant:
                    loc = f"({int(w.person.cx)},{int(w.person.cy)})"
                    print(f"    Worker #{i+1} at {loc}: {', '.join(w.violations)}")
        else:
            print("\n  All workers are wearing required PPE.")
        print(f"{'='*50}\n")