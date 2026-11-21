"""Statistics tracker: counts waste items by category and generates classification reports."""

import time
from collections import defaultdict
from typing import List, Optional

import cv2
import numpy as np

import config
from waste_detector import WasteDetection


class WasteStatistics:
    def __init__(self):
        self._counts = defaultdict(int)
        self._total = 0
        self._recyclable_count = 0
        self._non_recyclable_count = 0
        self._frame_count = 0
        self._session_start = time.time()
        self._category_history = defaultdict(list)
        self._logged_items = set()

    def update(self, detections: List[WasteDetection], frame_idx: int):
        self._frame_count += 1
        for det in detections:
            self._counts[det.category] += 1
            self._total += 1
            if det.recyclable:
                self._recyclable_count += 1
            else:
                self._non_recyclable_count += 1
            self._category_history[det.category].append(det.confidence)
            self._log_detection(det, frame_idx)

    def _log_detection(self, det: WasteDetection, frame_idx: int):
        if not config.ENABLE_LOG:
            return
        item_key = (det.category, det.x1, det.y1, det.x2, det.y2, frame_idx)
        if item_key in self._logged_items:
            return
        self._logged_items.add(item_key)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        line = (f"[{timestamp}] frame={frame_idx} category={det.category} "
                f"cls='{det.cls_name}' conf={det.confidence:.3f} "
                f"recyclable={det.recyclable} "
                f"box=({det.x1},{det.y1},{det.x2},{det.y2})\n")
        try:
            with open(config.STATS_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception as e:
            print(f"[Stats] Failed to write log: {e}")

    @property
    def counts(self) -> dict:
        return dict(self._counts)

    @property
    def total(self) -> int:
        return self._total

    @property
    def recyclable_count(self) -> int:
        return self._recyclable_count

    @property
    def non_recyclable_count(self) -> int:
        return self._non_recyclable_count

    @property
    def recyclable_rate(self) -> float:
        if self._total == 0:
            return 0.0
        return self._recyclable_count / self._total

    def get_percentages(self) -> dict:
        if self._total == 0:
            return {}
        return {cat: (count / self._total) * 100 for cat, count in self._counts.items()}

    def get_avg_confidence(self) -> dict:
        result = {}
        for cat, confs in self._category_history.items():
            if confs:
                result[cat] = sum(confs) / len(confs)
        return result

    def get_summary(self) -> dict:
        return {
            "total": self._total,
            "counts": dict(self._counts),
            "recyclable": self._recyclable_count,
            "non_recyclable": self._non_recyclable_count,
            "recyclable_rate": self.recyclable_rate,
            "frames": self._frame_count,
        }

    def print_report(self):
        elapsed = time.time() - self._session_start
        print(f"\n{'='*55}")
        print(f"  WASTE CLASSIFICATION REPORT")
        print(f"{'='*55}")
        print(f"  Frames processed      : {self._frame_count}")
        print(f"  Total items detected  : {self._total}")
        print(f"  Recyclable items      : {self._recyclable_count}")
        print(f"  Non-recyclable items  : {self._non_recyclable_count}")
        print(f"  Recyclable rate       : {self.recyclable_rate*100:.1f}%")
        print(f"  Session duration      : {elapsed:.1f}s")
        if self._counts:
            print(f"\n  {'Category':<12} {'Count':>6} {'Percent':>8} {'Avg Conf':>9}")
            print(f"  {'-'*12} {'-'*6} {'-'*8} {'-'*9}")
            avg_conf = self.get_avg_confidence()
            for cat in sorted(self._counts.keys()):
                count = self._counts[cat]
                pct = (count / self._total) * 100
                avg = avg_conf.get(cat, 0.0)
                print(f"  {cat:<12} {count:>6} {pct:>7.1f}% {avg:>8.1%}")
        print(f"{'='*55}\n")

    def draw_hud(self, frame: np.ndarray, current_detections: List[WasteDetection]) -> np.ndarray:
        h, w = frame.shape[:2]
        panel_h = 110
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, panel_h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, config.HUD_BG_ALPHA, frame, 1 - config.HUD_BG_ALPHA, 0, frame)

        cv2.putText(frame, "WASTE DETECTION & CLASSIFICATION SYSTEM", (10, 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

        cv2.putText(frame, f"Total: {self._total}  |  Recyclable: {self._recyclable_count}  |  Non-recyclable: {self._non_recyclable_count}",
                    (10, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        x_offset = 10
        for cat in config.WASTE_CATEGORIES:
            count = self._counts.get(cat, 0)
            info = config.WASTE_CATEGORIES[cat]
            color = info["color"]
            cv2.rectangle(frame, (x_offset, 62), (x_offset + 12, 74), color, -1)
            label = f"{cat[:4]}:{count}"
            cv2.putText(frame, label, (x_offset + 16, 73),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
            x_offset += 100

        cv2.putText(frame, f"Recyclable rate: {self.recyclable_rate*100:.1f}%",
                    (10, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        return frame

    def draw_annotations(self, frame: np.ndarray, detections: List[WasteDetection]) -> np.ndarray:
        annotated = frame.copy()

        if config.SHOW_CONVEYOR_GUIDE:
            h, w = annotated.shape[:2]
            belt_y = int(h * 0.5)
            cv2.line(annotated, (0, belt_y), (w, belt_y),
                     config.CONVEYOR_LINE_COLOR, 1)
            cv2.putText(annotated, "CONVEYOR", (10, belt_y - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, config.CONVEYOR_LINE_COLOR, 1)

        for det in detections:
            info = config.WASTE_CATEGORIES.get(det.category, config.WASTE_CATEGORIES[config.DEFAULT_CATEGORY])
            color = info["color"]

            cv2.rectangle(annotated, (det.x1, det.y1), (det.x2, det.y2), color, 3)

            label = f"{det.category.upper()} {det.confidence:.0%}"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX,
                                          config.CATEGORY_LABEL_FONT_SCALE,
                                          config.CATEGORY_LABEL_THICKNESS)
            label_y = det.y1 - th - 6 if det.y1 > th + 10 else det.y1 + th + 6
            label_bg_y1 = label_y - th - 4
            cv2.rectangle(annotated, (det.x1, label_bg_y1), (det.x1 + tw + 6, label_y + 4), color, -1)
            cv2.putText(annotated, label, (det.x1 + 3, label_y),
                        cv2.FONT_HERSHEY_SIMPLEX, config.CATEGORY_LABEL_FONT_SCALE,
                        (255, 255, 255), config.CATEGORY_LABEL_THICKNESS)

            icon = info["icon"]
            icon_x = det.x2 - 22
            icon_y = det.y1 + 18
            cv2.rectangle(annotated, (icon_x, det.y1), (det.x2, icon_y), (0, 0, 0), -1)
            cv2.putText(annotated, icon, (icon_x + 3, icon_y - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

            rec_mark = "R" if det.recyclable else "N"
            rec_color = (0, 255, 0) if det.recyclable else (0, 0, 255)
            cv2.circle(annotated, (det.x1 + 8, det.y2 - 8), 6, rec_color, -1)
            cv2.putText(annotated, rec_mark, (det.x1 + 5, det.y2 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

        return annotated