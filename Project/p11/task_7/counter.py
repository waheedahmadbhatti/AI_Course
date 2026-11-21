"""Crowd counter: tracks line crossings to count entries/exits and current crowd size."""

import math
import time
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

import config
from crowd_detector import TrackedPerson


class CrossingEvent:
    ENTRY = "ENTRY"
    EXIT = "EXIT"


class CrowdCounter:
    def __init__(self, line_position=None, orientation=None):
        self.orientation = orientation or config.COUNTING_LINE_ORIENTATION
        self._line_ratio = config.COUNTING_LINE_RATIO
        self._line_pos = line_position
        self._line_coord = None

        self._entered = 0
        self._exited = 0
        self._prev_positions: Dict[int, float] = {}
        self._active_tracks: Dict[int, TrackedPerson] = {}
        self._crossed_ids = set()
        self._events_log: List[Tuple[int, str, int]] = []
        self._frame_count = 0
        self._session_start = time.time()
        self._peak_count = 0

    def set_line(self, frame_width: int, frame_height: int):
        if self._line_pos is not None:
            self._line_coord = self._line_pos
        else:
            if self.orientation == "horizontal":
                self._line_coord = int(frame_height * self._line_ratio)
            else:
                self._line_coord = int(frame_width * self._line_ratio)

    @property
    def line_coord(self) -> int:
        return self._line_coord or 0

    @property
    def entered(self) -> int:
        return self._entered

    @property
    def exited(self) -> int:
        return self._exited

    @property
    def current_count(self) -> int:
        return len(self._active_tracks)

    @property
    def peak_count(self) -> int:
        return self._peak_count

    @property
    def net_flow(self) -> int:
        return self._entered - self._exited

    def update(self, persons: List[TrackedPerson], frame_idx: int) -> List[Tuple[int, str]]:
        self._frame_count += 1
        events = []

        current_ids = set()
        for person in persons:
            tid = person.track_id
            current_ids.add(tid)
            self._active_tracks[tid] = person

            if self.orientation == "horizontal":
                pos = person.cy
            else:
                pos = person.cx

            if tid in self._prev_positions:
                prev_pos = self._prev_positions[tid]
                crossing = self._check_crossing(prev_pos, pos)
                if crossing and tid not in self._crossed_ids:
                    self._crossed_ids.add(tid)
                    if crossing == CrossingEvent.ENTRY:
                        self._entered += 1
                    else:
                        self._exited += 1
                    events.append((tid, crossing))
                    self._events_log.append((frame_idx, crossing, tid))
                    self._log_event(frame_idx, crossing, tid, person)
            self._prev_positions[tid] = pos

        lost_ids = set(self._active_tracks.keys()) - current_ids
        for tid in lost_ids:
            del self._active_tracks[tid]
            self._prev_positions.pop(tid, None)
            self._crossed_ids.discard(tid)

        if self.current_count > self._peak_count:
            self._peak_count = self.current_count

        return events

    def _check_crossing(self, prev_pos: float, curr_pos: float) -> Optional[str]:
        line = self._line_coord
        if line is None:
            return None
        if prev_pos < line <= curr_pos:
            return CrossingEvent.ENTRY
        if prev_pos >= line > curr_pos:
            return CrossingEvent.EXIT
        return None

    def _log_event(self, frame_idx: int, event: str, track_id: int, person: TrackedPerson):
        if not config.ENABLE_LOG:
            return
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        line = (f"[{timestamp}] frame={frame_idx} event={event} "
                f"track_id={track_id} pos=({int(person.cx)},{int(person.cy)}) "
                f"conf={person.confidence:.3f}\n")
        try:
            with open(config.STATS_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception as e:
            print(f"[Counter] Failed to write log: {e}")

    def get_crowd_level(self) -> str:
        count = self.current_count
        if count >= config.CROWD_DANGER_THRESHOLD:
            return "DANGER"
        if count >= config.CROWD_WARNING_THRESHOLD:
            return "WARNING"
        return "NORMAL"

    def draw_counting_line(self, frame: np.ndarray) -> np.ndarray:
        if not config.SHOW_COUNTING_LINE or self._line_coord is None:
            return frame
        h, w = frame.shape[:2]
        color = config.COLORS["counting_line"]
        if self.orientation == "horizontal":
            y = self._line_coord
            cv2.line(frame, (0, y), (w, y), color, 2)
            cv2.putText(frame, "COUNTING LINE", (10, y - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            arrow_y = y + 20
            cv2.arrowedLine(frame, (w // 2, arrow_y), (w // 2, y - 5),
                            config.COLORS["entry"], 2, tipLength=0.3)
            cv2.putText(frame, "ENTRY", (w // 2 + 10, arrow_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, config.COLORS["entry"], 1)
            cv2.arrowedLine(frame, (w // 2 - 60, y - 5), (w // 2 - 60, arrow_y),
                            config.COLORS["exit"], 2, tipLength=0.3)
            cv2.putText(frame, "EXIT", (w // 2 - 100, arrow_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, config.COLORS["exit"], 1)
        else:
            x = self._line_coord
            cv2.line(frame, (x, 0), (x, h), color, 2)
            cv2.putText(frame, "COUNTING LINE", (x + 5, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        return frame

    def draw_tracks(self, frame: np.ndarray, persons: List[TrackedPerson]) -> np.ndarray:
        for person in persons:
            color = config.COLORS["person_tracked"]

            cv2.rectangle(frame, (person.x1, person.y1), (person.x2, person.y2), color, 2)

            label = f"ID:{person.track_id}"
            cv2.putText(frame, label, (person.x1, person.y1 - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

            if config.SHOW_TRACK_TRAILS and len(person.history) > 1:
                pts = list(person.history)
                for j in range(1, len(pts)):
                    alpha = j / len(pts)
                    trail_color = tuple(int(c * alpha) for c in color)
                    cv2.line(frame,
                             (int(pts[j - 1][0]), int(pts[j - 1][1])),
                             (int(pts[j][0]), int(pts[j][1])),
                             trail_color, 1)

            if config.SHOW_DIRECTION_ARROWS and len(person.history) >= 2:
                prev = person.history[-2]
                curr = person.history[-1]
                dx = curr[0] - prev[0]
                dy = curr[1] - prev[1]
                dist = math.hypot(dx, dy)
                if dist > 2:
                    arrow_end = (int(person.cx + dx * 3), int(person.cy + dy * 3))
                    cv2.arrowedLine(frame,
                                    (int(person.cx), int(person.cy)),
                                    arrow_end, color, 2, tipLength=0.4)

        return frame

    def draw_hud(self, frame: np.ndarray) -> np.ndarray:
        h, w = frame.shape[:2]
        panel_h = 120
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, panel_h), config.COLORS["hud_bg"], -1)
        cv2.addWeighted(overlay, config.HUD_BG_ALPHA, frame, 1 - config.HUD_BG_ALPHA, 0, frame)

        cv2.putText(frame, "CROWD MONITORING SYSTEM", (10, 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, config.COLORS["text"], 2)

        level = self.get_crowd_level()
        if level == "DANGER":
            level_color = config.COLORS["danger"]
        elif level == "WARNING":
            level_color = config.COLORS["warning"]
        else:
            level_color = config.COLORS["safe"]

        cv2.putText(frame, f"Current Crowd: {self.current_count}",
                    (10, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.6, level_color, 2)
        cv2.putText(frame, f"[{level}]",
                    (260, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.6, level_color, 2)

        cv2.putText(frame, f"Entered: {self._entered}   Exited: {self._exited}   Net: {self.net_flow}",
                    (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.55, config.COLORS["text_highlight"], 1)
        cv2.putText(frame, f"Peak: {self._peak_count}   Active tracks: {len(self._active_tracks)}",
                    (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.55, config.COLORS["text"], 1)

        if level != "NORMAL":
            msg = "CROWD WARNING!" if level == "WARNING" else "CROWD DANGER! OVER LIMIT!"
            cv2.rectangle(frame, (w - 300, 5), (w - 5, 35), level_color, -1)
            cv2.putText(frame, msg, (w - 295, 27),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

        return frame

    def print_report(self):
        elapsed = time.time() - self._session_start
        print(f"\n{'='*55}")
        print(f"  CROWD MONITORING REPORT")
        print(f"{'='*55}")
        print(f"  Frames processed     : {self._frame_count}")
        print(f"  Total entered        : {self._entered}")
        print(f"  Total exited         : {self._exited}")
        print(f"  Net flow             : {self.net_flow}")
        print(f"  Peak crowd count     : {self._peak_count}")
        print(f"  Current crowd        : {self.current_count}")
        print(f"  Session duration     : {elapsed:.1f}s")
        if self._events_log:
            print(f"\n  Crossing events ({len(self._events_log)} total):")
            for frame_idx, event, tid in self._events_log[-10:]:
                print(f"    Frame {frame_idx}: {event} (ID:{tid})")
            if len(self._events_log) > 10:
                print(f"    ... and {len(self._events_log) - 10} more")
        print(f"{'='*55}\n")