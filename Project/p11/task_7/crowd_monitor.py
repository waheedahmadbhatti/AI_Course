"""CrowdMonitor: orchestrates detection, tracking, and counting for crowd monitoring."""

from typing import List, Optional, Tuple

import cv2
import numpy as np

import config
from crowd_detector import CrowdDetector, TrackedPerson
from counter import CrowdCounter


class CrowdMonitor:
    def __init__(self, model_path=None, conf=None, iou=None,
                 line_position=None, orientation=None):
        self.detector = CrowdDetector(model_path=model_path, conf=conf, iou=iou)
        self.counter = CrowdCounter(line_position=line_position, orientation=orientation)
        self._frame_idx = 0
        self._line_initialized = False

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, List[TrackedPerson], List[Tuple[int, str]]]:
        self._frame_idx += 1

        if not self._line_initialized:
            h, w = frame.shape[:2]
            self.counter.set_line(w, h)
            self._line_initialized = True
            print(f"[Monitor] Counting line set at {self.counter.orientation}={self.counter.line_coord}")

        persons = self.detector.track(frame, self._frame_idx)

        for person in persons:
            person.update(person.x1, person.y1, person.x2, person.y2,
                          person.confidence, self._frame_idx)

        events = self.counter.update(persons, self._frame_idx)

        annotated = frame.copy()
        annotated = self.counter.draw_counting_line(annotated)
        annotated = self.counter.draw_tracks(annotated, persons)
        annotated = self.counter.draw_hud(annotated)

        return annotated, persons, events

    def run_on_image(self, image_path: str, output_path: Optional[str] = None) -> np.ndarray:
        frame = cv2.imread(image_path)
        if frame is None:
            raise FileNotFoundError(f"Cannot read image: {image_path}")
        annotated, persons, events = self.process_frame(frame)
        if output_path:
            cv2.imwrite(output_path, annotated)
            print(f"[Monitor] Saved annotated image to {output_path}")
        self._print_summary(persons)
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
                annotated, persons, events = self.process_frame(frame)
                if writer:
                    writer.write(annotated)
                if display:
                    cv2.imshow("Crowd Monitor (press 'q' to quit)", annotated)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q") or key == 27:
                        break
                frame_count += 1
                if events:
                    for tid, event in events:
                        print(f"[Monitor] Frame {frame_count}: {event} (ID:{tid}) | "
                              f"Crowd={self.counter.current_count}")
                if frame_count % 60 == 0:
                    print(f"[Monitor] Frame {frame_count}: crowd={len(persons)} "
                          f"entered={self.counter.entered} exited={self.counter.exited}")
        finally:
            cap.release()
            if writer:
                writer.release()
            if display:
                cv2.destroyAllWindows()

        self.counter.print_report()

    def _open_source(self, source):
        if isinstance(source, int):
            return cv2.VideoCapture(source, cv2.CAP_DSHOW)
        return cv2.VideoCapture(source)

    def _print_summary(self, persons: List[TrackedPerson]):
        print(f"\n{'='*55}")
        print(f"  CROWD DETECTION SUMMARY")
        print(f"{'='*55}")
        print(f"  People detected       : {len(persons)}")
        print(f"  Track IDs             : {[p.track_id for p in persons]}")
        print(f"  Entered               : {self.counter.entered}")
        print(f"  Exited                : {self.counter.exited}")
        print(f"  Current crowd         : {self.counter.current_count}")
        print(f"  Crowd level           : {self.counter.get_crowd_level()}")
        print(f"{'='*55}\n")