"""Alert system: visual annotations, audio beeps, and log file for safety violations."""

import os
import time
from collections import defaultdict
from typing import List

import cv2
import numpy as np

import config
from ppe_detector import WorkerStatus


class AlertSystem:
    def __init__(self):
        self._last_alert_time = defaultdict(float)
        self._violation_counts = {"NO HELMET": 0, "NO SAFETY VEST": 0}
        self._frame_count = 0
        self._total_violations = 0
        self._audio_available = self._check_audio()
        if config.ENABLE_LOG_ALERTS:
            log_path = config.ALERT_LOG_FILE
            os.makedirs(os.path.dirname(log_path), exist_ok=True)

    @staticmethod
    def _check_audio() -> bool:
        if not config.ENABLE_AUDIO_ALERTS:
            return False
        try:
            import winsound
            return True
        except ImportError:
            try:
                import simpleaudio
                return True
            except ImportError:
                return False

    def _beep(self):
        if not self._audio_available:
            return
        try:
            import winsound
            winsound.Beep(1000, 300)
        except Exception:
            try:
                import simpleaudio
                fs = 44100
                t = np.linspace(0, 0.3, int(fs * 0.3), False)
                wave = np.sin(2 * np.pi * 1000 * t) * 32767
                audio = wave.astype(np.int16)
                simpleaudio.play_buffer(audio, 1, 2, fs)
            except Exception:
                pass

    def _log_alert(self, message: str):
        if not config.ENABLE_LOG_ALERTS:
            return
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {message}\n"
        try:
            with open(config.ALERT_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception as e:
            print(f"[Alert] Failed to write log: {e}")

    def _should_alert(self, key: str) -> bool:
        now = time.time()
        if now - self._last_alert_time[key] >= config.ALERT_COOLDOWN_SECONDS:
            self._last_alert_time[key] = now
            return True
        return False

    def trigger(self, worker: WorkerStatus, frame_idx: int) -> List[str]:
        alerts = []
        if worker.is_compliant:
            return alerts

        person_id = f"worker_{frame_idx}_{int(worker.person.cx)}_{int(worker.person.cy)}"
        violations = worker.violations

        if "NO HELMET" in violations and "NO SAFETY VEST" in violations:
            msg = config.WARN_NO_BOTH
        elif "NO HELMET" in violations:
            msg = config.WARN_NO_HELMET
        elif "NO SAFETY VEST" in violations:
            msg = config.WARN_NO_VEST
        else:
            return alerts

        for v in violations:
            self._violation_counts[v] = self._violation_counts.get(v, 0) + 1
        self._total_violations += 1

        if self._should_alert(person_id):
            print(f"\a[ALERT] {msg} (conf={worker.person.confidence:.2f})")
            self._beep()
            self._log_alert(f"{msg} | location=({int(worker.person.cx)},{int(worker.person.cy)}) | conf={worker.person.confidence:.2f}")
        alerts.append(msg)
        return alerts

    def annotate(self, frame: np.ndarray, workers: List[WorkerStatus]) -> np.ndarray:
        annotated = frame.copy()
        self._frame_count += 1

        for worker in workers:
            p = worker.person
            if worker.is_compliant:
                color = config.COLORS["safe"]
                label = "SAFE"
            else:
                color = config.COLORS["warning"]
                label = " | ".join(worker.violations)

            cv2.rectangle(annotated, (p.x1, p.y1), (p.x2, p.y2), color, 3)

            head_y2 = p.y1 + int(p.height * config.HEAD_REGION_RATIO)
            cv2.line(annotated, (p.x1, head_y2), (p.x2, head_y2), (255, 255, 255), 1)
            torso_y2 = p.y1 + int(p.height * (config.HEAD_REGION_RATIO + config.TORSO_REGION_RATIO))
            cv2.line(annotated, (p.x1, torso_y2), (p.x2, torso_y2), (255, 255, 255), 1)

            if worker.helmet_det:
                h = worker.helmet_det
                hc = config.COLORS["helmet"] if worker.has_helmet else config.COLORS["no_helmet"]
                cv2.rectangle(annotated, (h.x1, h.y1), (h.x2, h.y2), hc, 2)
                cv2.putText(annotated, "Helmet", (h.x1, h.y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, hc, 1)

            if worker.vest_det:
                v = worker.vest_det
                vc = config.COLORS["vest"] if worker.has_vest else config.COLORS["no_vest"]
                cv2.rectangle(annotated, (v.x1, v.y1), (v.x2, v.y2), vc, 2)
                cv2.putText(annotated, "Vest", (v.x1, v.y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, vc, 1)

            label_y = p.y1 - 10 if p.y1 > 25 else p.y1 + 20
            cv2.putText(annotated, label, (p.x1, label_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            status_parts = []
            status_parts.append(f"H:{'Y' if worker.has_helmet else 'N'}")
            status_parts.append(f"V:{'Y' if worker.has_vest else 'N'}")
            status_text = " ".join(status_parts)
            cv2.putText(annotated, status_text, (p.x1, p.y2 + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        self._draw_hud(annotated, workers)
        return annotated

    def _draw_hud(self, frame: np.ndarray, workers: List[WorkerStatus]):
        h, w = frame.shape[:2]
        total = len(workers)
        compliant = sum(1 for w in workers if w.is_compliant)
        violators = total - compliant

        panel_h = 70
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, panel_h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

        cv2.putText(frame, "CONSTRUCTION SITE SAFETY MONITOR", (10, 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Workers: {total}  |  Compliant: {compliant}  |  Violations: {violators}",
                    (10, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1)

        if violators > 0:
            cv2.rectangle(frame, (w - 180, 5), (w - 5, 35), (0, 0, 200), -1)
            cv2.putText(frame, f"!! {violators} ALERT(S) !!", (w - 175, 27),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    @property
    def stats(self) -> dict:
        return {
            "frames_processed": self._frame_count,
            "total_violations": self._total_violations,
            "no_helmet_count": self._violation_counts.get("NO HELMET", 0),
            "no_vest_count": self._violation_counts.get("NO SAFETY VEST", 0),
        }