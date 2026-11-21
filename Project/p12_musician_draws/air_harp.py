"""Air Harp - a hand-tracking virtual harp using MediaPipe + OpenCV + pygame.

Pinch both hands to draw a glowing string. Touch (pluck) a string with your
index fingertip to play a note. Longer strings play lower notes (C-major
pentatonic). Keys: c = clear, q or ESC = quit.
"""

import time
import math
import sys

import cv2
import numpy as np
import mediapipe as mp
import pygame
import pygame.sndarray

# ----- MediaPipe legacy API setup -----
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles

hands = mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.6,
)

# ----- pygame sound setup -----
pygame.mixer.pre_init(frequency=44100, size=-16, channels=1)
pygame.mixer.init()
SOUND_FREQ = 44100

# Note names and frequencies for C-major pentatonic (low -> high).
NOTE_NAMES = ["C4", "D4", "E4", "G4", "A4", "C5", "D5", "E5"]
NOTE_FREQS = [261.63, 293.66, 329.63, 392.00, 440.00, 523.25, 587.33, 659.25]


def make_note(freq, duration=0.8, freq_rate=SOUND_FREQ):
    """Generate a sine + 2nd harmonic note with exp decay envelope, return pygame Sound."""
    n = int(freq_rate * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    # Fundamental + 2nd harmonic (half amplitude).
    wave = np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(2 * np.pi * 2 * freq * t)
    # Exponential decay envelope.
    envelope = np.exp(-3.0 * t)
    wave = wave * envelope
    # Normalize to avoid clipping.
    wave = wave / np.max(np.abs(wave)) * 0.9
    # Convert to int16.
    audio = (wave * 32767).astype(np.int16)
    # Shape array to match the mixer's actual channel count (mono or stereo).
    channels = pygame.mixer.get_init()[2]
    if channels == 2:
        audio = np.column_stack((audio, audio))
    else:
        audio = audio.reshape(-1, 1)
    return pygame.sndarray.make_sound(audio)


# Pre-generate all notes.
NOTES = [make_note(f) for f in NOTE_FREQS]


def point_to_segment_dist(px, py, x1, y1, x2, y2):
    """Shortest distance from point (px,py) to segment (x1,y1)-(x2,y2)."""
    dx, dy = x2 - x1, y2 - y1
    seg_len2 = dx * dx + dy * dy
    if seg_len2 == 0:
        return math.hypot(px - x1, py - y1), 0.0
    t = ((px - x1) * dx + (py - y1) * dy) / seg_len2
    t = max(0.0, min(1.0, t))
    cx, cy = x1 + t * dx, y1 + t * dy
    return math.hypot(px - cx, py - cy), t


def assign_note_color(idx, total):
    """Pick a bright HSV color for string idx (total strings)."""
    hue = int(180 * idx / max(1, total)) % 180
    color_hsv = np.uint8([[[hue, 255, 255]]])
    color_bgr = cv2.cvtColor(color_hsv, cv2.COLOR_HSV2BGR)[0][0]
    return tuple(int(c) for c in color_bgr)


def draw_glowing_string(frame, p1, p2, color, thickness_glow=12, thickness_core=2):
    """Draw a glowing colored string: blurred thick line + thin white core."""
    overlay = np.zeros_like(frame)
    cv2.line(overlay, p1, p2, color, thickness=thickness_glow)
    blurred = cv2.GaussianBlur(overlay, (21, 21), 0)
    cv2.addWeighted(blurred, 1.0, frame, 1.0, 0, dst=frame)
    cv2.line(frame, p1, p2, (255, 255, 255), thickness=thickness_core)


def draw_vibrating_string(frame, p1, p2, color, phase, amplitude):
    """Draw a string wobbling as a sine curve. amplitude decays externally."""
    x1, y1 = p1
    x2, y2 = p2
    pts = []
    for i in range(30):
        t = i / 29.0
        bx = x1 + (x2 - x1) * t
        by = y1 + (y2 - y1) * t
        # Perpendicular offset scaled by sine and a tent function (0 at ends).
        offset = amplitude * math.sin(2 * math.pi * 3 * t + phase) * math.sin(math.pi * t)
        # Perpendicular direction.
        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / length, dx / length
        pts.append((int(bx + nx * offset), int(by + ny * offset)))
    pts = np.array(pts, dtype=np.int32)
    overlay = np.zeros_like(frame)
    cv2.polylines(overlay, [pts], False, color, thickness=12)
    blurred = cv2.GaussianBlur(overlay, (21, 21), 0)
    cv2.addWeighted(blurred, 1.0, frame, 1.0, 0, dst=frame)
    cv2.polylines(frame, [pts], False, (255, 255, 255), thickness=2)


class StringObj:
    """A saved harp string with note + vibration state."""
    def __init__(self, p1, p2, color, note_idx):
        self.p1 = p1
        self.p2 = p2
        self.color = color
        self.note_idx = note_idx
        self.length = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        self.last_pluck = 0.0       # time of last pluck
        self.vib_start = 0.0        # time vibration started
        self.vib_amp = 0.0          # current amplitude (set on pluck)
        self.vib_duration = 0.6

    def pluck(self, now):
        if now - self.last_pluck >= 0.25:
            self.last_pluck = now
            self.vib_start = now
            self.vib_amp = 15.0
            NOTES[self.note_idx].play()
            return NOTE_NAMES[self.note_idx]
        return None

    def amplitude_now(self, now):
        elapsed = now - self.vib_start
        if elapsed >= self.vib_duration or self.vib_amp == 0.0:
            return 0.0
        return self.vib_amp * (1.0 - elapsed / self.vib_duration)


def main():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    if not cap.isOpened():
        print("ERROR: Could not open webcam index 0.")
        print("If on macOS and OpenCV says 'not authorized to capture video',")
        print("enable Camera for Terminal (or CodeArts) in System Settings ->")
        print("Privacy & Security -> Camera, then rerun from the macOS Terminal app.")
        return

    strings = []
    drawing_midpoint = None     # current live pinch midpoint (per frame, both hands)
    drawing_active = False
    # Track per-hand pinch state and last midpoint for live line drawing.
    live_p1 = None              # one hand's pinch midpoint
    live_p2 = None              # other hand's pinch midpoint
    live_prev = None            # previous frame's (p1,p2) for release detection

    # Per-hand smoothed fingertip positions (EMA, alpha=0.5).
    smoothed_tips = {}          # hand_idx -> (x,y)
    ALPHA = 0.5

    # Per-hand per-string previous signed distance for pluck crossing detection.
    prev_dists = {}             # hand_idx -> {string_id -> signed dist}

    last_note = "-"
    prev_time = time.time()
    fps = 0.0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("ERROR: failed to grab frame.")
                break

            # Mirror horizontally.
            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]

            # Convert to RGB for MediaPipe.
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)

            now = time.time()
            # FPS calc.
            dt = now - prev_time
            prev_time = now
            if dt > 0:
                fps = 0.9 * fps + 0.1 * (1.0 / dt)

            # ----- Detect pinches on both hands -----
            pinch_points = []   # list of (x,y) pinch midpoints in px
            tip_points = []     # list of smoothed index fingertip (x,y)
            hand_count = 0

            if results.multi_hand_landmarks:
                for hand_idx, hand_lms in enumerate(results.multi_hand_landmarks):
                    hand_count += 1
                    # Draw skeleton (green lines, red points via default styles).
                    mp_drawing.draw_landmarks(
                        frame,
                        hand_lms,
                        mp_hands.HAND_CONNECTIONS,
                        mp_styles.get_default_hand_landmarks_style(),
                        mp_styles.get_default_hand_connections_style(),
                    )

                    lms = hand_lms.landmark
                    thumb = (int(lms[4].x * w), int(lms[4].y * h))
                    index = (int(lms[8].x * w), int(lms[8].y * h))

                    # EMA smoothing on index fingertip.
                    if hand_idx in smoothed_tips:
                        sx, sy = smoothed_tips[hand_idx]
                        sx = ALPHA * index[0] + (1 - ALPHA) * sx
                        sy = ALPHA * index[1] + (1 - ALPHA) * sy
                    else:
                        sx, sy = index
                    smoothed_tips[hand_idx] = (sx, sy)
                    tip_points.append((sx, sy))

                    # Pinch detection.
                    pinch_dist = math.hypot(thumb[0] - index[0], thumb[1] - index[1])
                    if pinch_dist < 40:
                        mid = ((thumb[0] + index[0]) / 2.0,
                               (thumb[1] + index[1]) / 2.0)
                        pinch_points.append(mid)

                    # Draw pinch marker.
                    cv2.circle(frame, thumb, 6, (0, 0, 255), -1)
                    cv2.circle(frame, index, 6, (0, 0, 255), -1)

            # ----- Live string creation -----
            if len(pinch_points) >= 2:
                # Both hands pinching: draw live glowing line between midpoints.
                live_p1 = (int(pinch_points[0][0]), int(pinch_points[0][1]))
                live_p2 = (int(pinch_points[1][0]), int(pinch_points[1][1]))
                drawing_active = True
                draw_glowing_string(frame, live_p1, live_p2, (0, 255, 255))
            else:
                # Released: if we had a live line, save it as a string.
                if drawing_active and live_p1 is not None and live_p2 is not None:
                    length = math.hypot(live_p2[0] - live_p1[0],
                                        live_p2[1] - live_p1[1])
                    if length >= 80:
                        # Assign note: longer string -> lower note.
                        # We'll assign after sorting all strings by length.
                        color = assign_note_color(len(strings), 8)
                        s = StringObj(live_p1, live_p2, color, note_idx=0)
                        strings.append(s)
                        if len(strings) > 8:
                            strings.pop(0)
                        # Re-assign notes by length (longest=lowest note).
                        sorted_idx = sorted(range(len(strings)),
                                            key=lambda i: strings[i].length,
                                            reverse=True)
                        for slot, si in enumerate(sorted_idx):
                            note_pos = int(slot * len(NOTES) / len(strings))
                            note_pos = min(note_pos, len(NOTES) - 1)
                            strings[si].note_idx = note_pos
                            strings[si].color = assign_note_color(slot, len(strings))
                drawing_active = False
                live_p1 = None
                live_p2 = None

            # ----- Draw saved strings (with vibration) -----
            for s in strings:
                amp = s.amplitude_now(now)
                if amp > 0.0:
                    phase = (now - s.vib_start) * 20.0
                    draw_vibrating_string(frame, s.p1, s.p2, s.color, phase, amp)
                else:
                    draw_glowing_string(frame, s.p1, s.p2, s.color)

            # ----- Pluck detection -----
            # Build a stable id for each string (its index in list).
            for hand_idx, tip in enumerate(tip_points):
                tx, ty = tip
                if hand_idx not in prev_dists:
                    prev_dists[hand_idx] = {}
                for sid, s in enumerate(strings):
                    dist, t = point_to_segment_dist(tx, ty,
                                                    s.p1[0], s.p1[1],
                                                    s.p2[0], s.p2[1])
                    # Signed distance: which side of the segment.
                    dx, dy = s.p2[0] - s.p1[0], s.p2[1] - s.p1[1]
                    cross = (dx) * (ty - s.p1[1]) - (dy) * (tx - s.p1[0])
                    seg_len = math.hypot(dx, dy) or 1.0
                    signed = cross / seg_len
                    prev = prev_dists[hand_idx].get(sid, None)
                    # Crossing/within 12 px and was previously >20 px on a side.
                    if prev is not None:
                        crossed = (prev * signed < 0) or (abs(signed) < 12)
                        was_far = abs(prev) > 20
                        if crossed and was_far:
                            note = s.pluck(now)
                            if note:
                                last_note = note
                    prev_dists[hand_idx][sid] = signed
            # Clean prev_dists for hands no longer visible.
            for hid in list(prev_dists.keys()):
                if hid >= hand_count:
                    del prev_dists[hid]

            # ----- HUD -----
            cv2.rectangle(frame, (0, 0), (300, 70), (0, 0, 0), -1)
            cv2.putText(frame, f"FPS: {fps:4.1f}", (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, f"Strings: {len(strings)}", (10, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, f"Last: {last_note}", (160, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

            cv2.rectangle(frame, (0, h - 40), (w, h), (0, 0, 0), -1)
            cv2.putText(frame,
                        "Pinch both hands to draw | Touch string to play | C clear | Q quit",
                        (10, h - 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            cv2.imshow("Air Harp", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break
            elif key == ord('c'):
                strings.clear()
                last_note = "-"
    finally:
        cap.release()
        cv2.destroyAllWindows()
        pygame.mixer.quit()
        pygame.quit()


if __name__ == "__main__":
    main()