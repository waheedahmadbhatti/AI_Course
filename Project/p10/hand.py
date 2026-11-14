import os
import cv2
import mediapipe as mp
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import threading
import urllib.request
import time
import math

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hand_landmarker.task")

from mediapipe.tasks.python import vision

HAND_CONNECTIONS = vision.HandLandmarksConnections.HAND_CONNECTIONS

TIP_IDS = [4, 8, 12, 16, 20]
PIP_IDS = [3, 6, 10, 14, 18]
MCP_IDS = [2, 5, 9, 13, 17]
FINGER_NAMES = ["Thumb", "Index", "Middle", "Ring", "Pinky"]

FINGER_COLORS = [
    (255, 80, 80),
    (80, 220, 255),
    (80, 255, 120),
    (220, 100, 255),
    (255, 180, 60),
]

GESTURE_LIST = [
    "Fist", "Open Hand", "Peace / Victory", "Thumbs Up", "Thumbs Down",
    "Pointing", "OK Sign", "Rock / Horns", "Call Me", "Gun",
    "Three Fingers", "Four Fingers", "Pinch", "Vulcan Salute",
    "Spider-Man", "High Five", "Stop", "Snap",
]

BG_DARK = "#0f1117"
BG_PANEL = "#1a1d27"
BG_CARD = "#222632"
ACCENT = "#00d4aa"
ACCENT2 = "#3b82f6"
TEXT_PRIMARY = "#e8eaf0"
TEXT_SECONDARY = "#9aa0b4"
TEXT_DIM = "#6b7185"
DANGER = "#ff5b6e"
WARNING = "#ffb347"


def ensure_model():
    if os.path.exists(MODEL_PATH):
        return True
    try:
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        return True
    except Exception as e:
        print(f"Failed to download model: {e}")
        return False


def distance(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def get_fingers_up(landmarks):
    fingers_up = []
    for i in range(5):
        tip = landmarks[TIP_IDS[i]]
        pip = landmarks[PIP_IDS[i]]
        if i == 0:
            fingers_up.append(tip.x < pip.x)
        else:
            fingers_up.append(tip.y < pip.y)
    return fingers_up


def describe_position(fingers_up):
    count = sum(fingers_up)
    up_names = [FINGER_NAMES[i] for i in range(5) if fingers_up[i]]
    if count == 0:
        return "Hand Closed (Fist)"
    if count == 5:
        return "Hand Fully Open"
    if count == 1:
        return f"1 Finger Open — {up_names[0]}"
    return f"{count} Fingers Open — " + ", ".join(up_names)


def detect_gesture(landmarks):
    fingers_up = get_fingers_up(landmarks)
    count = sum(fingers_up)

    thumb_tip = landmarks[4]
    index_tip = landmarks[8]
    middle_tip = landmarks[12]
    ring_tip = landmarks[16]
    pinky_tip = landmarks[20]
    thumb_mcp = landmarks[2]

    thumb_index_dist = distance(thumb_tip, index_tip)

    if count == 0:
        return "Fist"

    if thumb_index_dist < 0.05 and fingers_up[2] and fingers_up[3] and fingers_up[4]:
        return "OK Sign"

    if fingers_up[0] and not fingers_up[1] and not fingers_up[2] and not fingers_up[3] and not fingers_up[4]:
        if thumb_tip.y < thumb_mcp.y:
            return "Thumbs Up"
        return "Thumbs Down"

    if not fingers_up[0] and fingers_up[1] and not fingers_up[2] and not fingers_up[3] and not fingers_up[4]:
        return "Pointing"

    if fingers_up[1] and fingers_up[2] and not fingers_up[3] and not fingers_up[4]:
        return "Peace / Victory"

    if not fingers_up[0] and fingers_up[1] and not fingers_up[2] and not fingers_up[3] and fingers_up[4]:
        return "Rock / Horns"

    if fingers_up[0] and not fingers_up[1] and not fingers_up[2] and not fingers_up[3] and fingers_up[4]:
        return "Call Me"

    if fingers_up[0] and fingers_up[1] and not fingers_up[2] and not fingers_up[3] and not fingers_up[4]:
        return "Gun"

    if not fingers_up[0] and fingers_up[1] and fingers_up[2] and fingers_up[3] and not fingers_up[4]:
        return "Three Fingers"

    if not fingers_up[0] and fingers_up[1] and fingers_up[2] and fingers_up[3] and fingers_up[4]:
        return "Four Fingers"

    if count == 5:
        return "Open Hand"

    if thumb_index_dist < 0.07 and not fingers_up[2] and not fingers_up[3] and not fingers_up[4]:
        return "Pinch"

    if fingers_up[1] and fingers_up[2] and fingers_up[3] and fingers_up[4]:
        mid_gap = abs(landmarks[12].x - landmarks[8].x)
        ring_gap = abs(landmarks[16].x - landmarks[12].x)
        if mid_gap > 0.06 and ring_gap > 0.06:
            return "Vulcan Salute"
        return "High Five"

    if fingers_up[0] and fingers_up[1] and not fingers_up[2] and fingers_up[3] and not fingers_up[4]:
        return "Spider-Man"

    if not fingers_up[0] and fingers_up[1] and fingers_up[2] and not fingers_up[3] and not fingers_up[4]:
        if middle_tip.y < landmarks[9].y:
            return "Stop"

    return f"{count} Fingers Up"


def draw_hand(frame, landmarks, w, h, handedness_label=""):
    pts = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]

    for finger_idx in range(5):
        chain = [MCP_IDS[finger_idx], PIP_IDS[finger_idx], TIP_IDS[finger_idx]]
        for k in range(len(chain) - 1):
            cv2.line(frame, pts[chain[k]], pts[chain[k + 1]], FINGER_COLORS[finger_idx], 3)

    palm_pts = [0, 2, 5, 9, 13, 17]
    for k in range(len(palm_pts) - 1):
        cv2.line(frame, pts[palm_pts[k]], pts[palm_pts[k + 1]], (180, 180, 200), 2)
    cv2.line(frame, pts[17], pts[0], (180, 180, 200), 2)

    for idx, p in enumerate(pts):
        if idx in TIP_IDS:
            cv2.circle(frame, p, 8, (0, 0, 255), -1)
            cv2.circle(frame, p, 8, (255, 255, 255), 1)
        else:
            cv2.circle(frame, p, 4, (255, 255, 255), -1)

    if handedness_label:
        cv2.putText(frame, handedness_label, (pts[0][0] - 20, pts[0][1] + 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2, cv2.LINE_AA)


class HandDetectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hand Posture Detection  ·  MediaPipe + OpenCV")
        self.root.geometry("1180x760")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_DARK)

        self.running = False
        self.cap = None
        self.landmarker = None
        self.mirror = True
        self.show_landmarks = True
        self.show_info = True
        self.recording = False
        self.writer = None
        self.snapshot_count = 0
        self.fps = 0.0
        self._prev_time = 0.0
        self._frame_times = []
        self._last_frame = None

        self._setup_theme()
        self._build_ui()

    def _setup_theme(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", background=BG_DARK, foreground=TEXT_PRIMARY,
                        font=("Segoe UI", 10))
        style.configure("TFrame", background=BG_DARK)
        style.configure("Panel.TFrame", background=BG_PANEL)
        style.configure("Card.TFrame", background=BG_CARD)
        style.configure("TLabel", background=BG_DARK, foreground=TEXT_PRIMARY)
        style.configure("Panel.TLabel", background=BG_PANEL, foreground=TEXT_PRIMARY)
        style.configure("Card.TLabel", background=BG_CARD, foreground=TEXT_PRIMARY)
        style.configure("Dim.TLabel", background=BG_PANEL, foreground=TEXT_DIM, font=("Segoe UI", 9))
        style.configure("Title.TLabel", background=BG_DARK, foreground=ACCENT,
                        font=("Segoe UI", 16, "bold"))
        style.configure("Subtitle.TLabel", background=BG_DARK, foreground=TEXT_SECONDARY,
                        font=("Segoe UI", 9))
        style.configure("Gesture.TLabel", background=BG_CARD, foreground=ACCENT,
                        font=("Segoe UI", 20, "bold"))
        style.configure("Stat.TLabel", background=BG_CARD, foreground=TEXT_PRIMARY,
                        font=("Segoe UI", 11, "bold"))
        style.configure("StatVal.TLabel", background=BG_CARD, foreground=ACCENT2,
                        font=("Segoe UI", 14, "bold"))
        style.configure("Section.TLabel", background=BG_PANEL, foreground=ACCENT,
                        font=("Segoe UI", 10, "bold"))

        style.configure("Accent.TButton", background=ACCENT, foreground="#0a0a0a",
                        font=("Segoe UI", 10, "bold"), borderwidth=0, padding=8)
        style.map("Accent.TButton",
                  background=[("active", "#00b894"), ("disabled", "#2a2d3a")],
                  foreground=[("disabled", TEXT_DIM)])

        style.configure("Danger.TButton", background=DANGER, foreground="#ffffff",
                        font=("Segoe UI", 10, "bold"), borderwidth=0, padding=8)
        style.map("Danger.TButton", background=[("active", "#e04856")])

        style.configure("Toggle.TButton", background=BG_CARD, foreground=TEXT_PRIMARY,
                        font=("Segoe UI", 9), borderwidth=0, padding=6)
        style.map("Toggle.TButton",
                  background=[("active", "#2d3142")],
                  foreground=[("active", ACCENT)])

        style.configure("TScrollbar", background=BG_PANEL, troughcolor=BG_DARK,
                        borderwidth=0, arrowcolor=TEXT_DIM)

    def _build_ui(self):
        header = ttk.Frame(self.root, style="Panel.TFrame")
        header.pack(fill=tk.X)
        ttk.Frame(header, height=3).pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Label(header, text="  ✋  Hand Posture Detection",
                  style="Title.TLabel").pack(side=tk.LEFT, padx=12, pady=10)
        ttk.Label(header, text="MediaPipe Tasks  ·  OpenCV  ·  Tkinter",
                  style="Subtitle.TLabel").pack(side=tk.LEFT, padx=4, pady=10)

        controls = ttk.Frame(self.root, style="Panel.TFrame")
        controls.pack(fill=tk.X, padx=10, pady=(8, 4))

        self.start_btn = ttk.Button(controls, text="▶  Start", style="Accent.TButton", command=self.start)
        self.start_btn.pack(side=tk.LEFT, padx=4, pady=8)

        self.stop_btn = ttk.Button(controls, text="■  Stop", style="Danger.TButton", command=self.stop, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=4, pady=8)

        self.snapshot_btn = ttk.Button(controls, text="📷  Snapshot", style="Toggle.TButton",
                                       command=self.save_snapshot, state=tk.DISABLED)
        self.snapshot_btn.pack(side=tk.LEFT, padx=4, pady=8)

        self.record_btn = ttk.Button(controls, text="●  Record", style="Toggle.TButton",
                                     command=self.toggle_record, state=tk.DISABLED)
        self.record_btn.pack(side=tk.LEFT, padx=4, pady=8)

        self.mirror_btn = ttk.Button(controls, text="🪞  Mirror: ON", style="Toggle.TButton", command=self.toggle_mirror)
        self.mirror_btn.pack(side=tk.LEFT, padx=4, pady=8)

        self.landmarks_btn = ttk.Button(controls, text="🦴  Landmarks: ON", style="Toggle.TButton",
                                        command=self.toggle_landmarks)
        self.landmarks_btn.pack(side=tk.LEFT, padx=4, pady=8)

        self.clear_btn = ttk.Button(controls, text="🗑  Clear Logs", style="Toggle.TButton", command=self.clear_logs)
        self.clear_btn.pack(side=tk.LEFT, padx=4, pady=8)

        self.exit_btn = ttk.Button(controls, text="✕  Exit", style="Danger.TButton", command=self.on_exit)
        self.exit_btn.pack(side=tk.RIGHT, padx=4, pady=8)

        body = ttk.Frame(self.root)
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

        video_wrap = ttk.Frame(body, style="Card.TFrame")
        video_wrap.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))
        self.video_label = tk.Label(video_wrap, bg="#000000")
        self.video_label.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        sidebar = ttk.Frame(body, style="Panel.TFrame", width=340)
        sidebar.pack(side=tk.RIGHT, fill=tk.Y)
        sidebar.pack_propagate(False)

        gesture_card = ttk.Frame(sidebar, style="Card.TFrame", padding=12)
        gesture_card.pack(fill=tk.X, padx=8, pady=(8, 4))
        ttk.Label(gesture_card, text="CURRENT GESTURE", style="Dim.TLabel").pack(anchor=tk.W)
        self.gesture_var = tk.StringVar(value="—")
        ttk.Label(gesture_card, textvariable=self.gesture_var, style="Gesture.TLabel").pack(anchor=tk.W, pady=(4, 0))

        stats_card = ttk.Frame(sidebar, style="Card.TFrame", padding=12)
        stats_card.pack(fill=tk.X, padx=8, pady=4)

        ttk.Label(stats_card, text="LIVE STATS", style="Dim.TLabel").pack(anchor=tk.W)
        stats_row = ttk.Frame(stats_card, style="Card.TFrame")
        stats_row.pack(fill=tk.X, pady=(6, 0))

        for col, (label, var_attr) in enumerate([
            ("FPS", "fps_var"), ("Hands", "hands_var"), ("Conf.", "conf_var")
        ]):
            cell = ttk.Frame(stats_row, style="Card.TFrame")
            cell.grid(row=0, column=col, sticky="nsew", padx=2)
            stats_row.grid_columnconfigure(col, weight=1)
            setattr(self, var_attr, tk.StringVar(value="0"))
            ttk.Label(cell, text=label, style="Dim.TLabel").pack(anchor=tk.W)
            ttk.Label(cell, textvariable=getattr(self, var_attr), style="StatVal.TLabel").pack(anchor=tk.W)

        info_card = ttk.Frame(sidebar, style="Card.TFrame", padding=12)
        info_card.pack(fill=tk.X, padx=8, pady=4)
        ttk.Label(info_card, text="HAND DETAILS", style="Dim.TLabel").pack(anchor=tk.W)
        self.info_var = tk.StringVar(value="No hand detected")
        ttk.Label(info_card, textvariable=self.info_var, style="Card.TLabel",
                  justify=tk.LEFT, font=("Segoe UI", 9)).pack(anchor=tk.W, pady=(4, 0))

        finger_card = ttk.Frame(sidebar, style="Card.TFrame", padding=12)
        finger_card.pack(fill=tk.X, padx=8, pady=4)
        ttk.Label(finger_card, text="FINGER STATES", style="Dim.TLabel").pack(anchor=tk.W)
        self.finger_vars = []
        finger_grid = ttk.Frame(finger_card, style="Card.TFrame")
        finger_grid.pack(fill=tk.X, pady=(4, 0))
        for i, name in enumerate(FINGER_NAMES):
            row = ttk.Frame(finger_grid, style="Card.TFrame")
            row.pack(fill=tk.X, pady=1)
            dot = tk.Label(row, text="●", fg=TEXT_DIM, bg=BG_CARD, font=("Segoe UI", 10))
            dot.pack(side=tk.LEFT, padx=(0, 6))
            ttk.Label(row, text=name, style="Card.TLabel", font=("Segoe UI", 9)).pack(side=tk.LEFT)
            sv = tk.StringVar(value="—")
            ttk.Label(row, textvariable=sv, style="Card.TLabel",
                      font=("Segoe UI", 9, "bold")).pack(side=tk.RIGHT)
            self.finger_vars.append((dot, sv))

        log_card = ttk.Frame(sidebar, style="Card.TFrame", padding=10)
        log_card.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        ttk.Label(log_card, text="GESTURE LOG", style="Dim.TLabel").pack(anchor=tk.W)
        self.gesture_log = tk.Text(log_card, height=5, font=("Consolas", 8),
                                   bg="#16181f", fg=ACCENT, insertbackground=ACCENT,
                                   borderwidth=0, padx=6, pady=4, state=tk.DISABLED)
        self.gesture_log.pack(fill=tk.BOTH, expand=True, pady=(4, 6))

        ttk.Label(log_card, text="POSITION LOG", style="Dim.TLabel").pack(anchor=tk.W)
        self.position_log = tk.Text(log_card, height=5, font=("Consolas", 8),
                                    bg="#16181f", fg=ACCENT2, insertbackground=ACCENT2,
                                    borderwidth=0, padx=6, pady=4, state=tk.DISABLED)
        self.position_log.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

        footer = ttk.Frame(self.root, style="Panel.TFrame")
        footer.pack(fill=tk.X, padx=10, pady=(4, 8))
        self.status_var = tk.StringVar(value="Ready — click Start to begin")
        ttk.Label(footer, textvariable=self.status_var, style="Panel.TLabel",
                  font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=10, pady=6)
        ttk.Label(footer, text=f"{len(GESTURE_LIST)} gestures  ·  21 landmarks/hand  ·  up to 2 hands",
                  style="Dim.TLabel").pack(side=tk.RIGHT, padx=10, pady=6)

    def toggle_mirror(self):
        self.mirror = not self.mirror
        self.mirror_btn.config(text=f"🪞  Mirror: {'ON' if self.mirror else 'OFF'}")

    def toggle_landmarks(self):
        self.show_landmarks = not self.show_landmarks
        self.landmarks_btn.config(text=f"🦴  Landmarks: {'ON' if self.show_landmarks else 'OFF'}")

    def toggle_record(self):
        if not self.running:
            return
        if not self.recording:
            path = filedialog.asksaveasfilename(defaultextension=".avi",
                                                filetypes=[("AVI Video", "*.avi")],
                                                initialfile="hand_record.avi")
            if not path:
                return
            fourcc = cv2.VideoWriter_fourcc(*"XVID")
            self.writer = cv2.VideoWriter(path, fourcc, 20.0, (640, 480))
            self.recording = True
            self.record_btn.config(text="●  Recording...")
            self.status_var.set(f"Recording to {path}")
        else:
            self.recording = False
            if self.writer:
                self.writer.release()
                self.writer = None
            self.record_btn.config(text="●  Record")
            self.status_var.set("Recording stopped")

    def clear_logs(self):
        for widget in (self.gesture_log, self.position_log):
            widget.config(state=tk.NORMAL)
            widget.delete(1.0, tk.END)
            widget.config(state=tk.DISABLED)

    def append_log(self, widget, text):
        widget.config(state=tk.NORMAL)
        widget.insert(tk.END, text + "\n")
        widget.see(tk.END)
        widget.config(state=tk.DISABLED)

    def save_snapshot(self):
        if self._last_frame is None:
            return
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg")],
            initialfile=f"hand_snapshot_{self.snapshot_count:03d}.png")
        if filename:
            cv2.imwrite(filename, self._last_frame)
            self.snapshot_count += 1
            self.status_var.set(f"Snapshot saved: {filename}")

    def start(self):
        if self.running:
            return
        if not ensure_model():
            messagebox.showerror("Error",
                                 f"Could not download model to:\n{MODEL_PATH}\n"
                                 f"Download manually from:\n{MODEL_URL}")
            return

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Could not open webcam.")
            self.cap = None
            return

        options = vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=MODEL_PATH),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=0.6,
            min_hand_presence_confidence=0.6,
            min_tracking_confidence=0.5,
        )
        self.landmarker = vision.HandLandmarker.create_from_options(options)

        self.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.snapshot_btn.config(state=tk.NORMAL)
        self.record_btn.config(state=tk.NORMAL)
        self.status_var.set("Running — show your hand to the webcam")
        self._prev_time = time.time()
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        timestamp = 0
        last_gesture = ""
        last_position = ""
        gesture_cooldown = 0
        position_cooldown = 0

        while self.running and self.cap is not None:
            ret, frame = self.cap.read()
            if not ret:
                break

            if self.mirror:
                frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            timestamp += 1
            result = self.landmarker.detect_for_video(mp_image, timestamp)

            num_hands = len(result.hand_landmarks) if result.hand_landmarks else 0
            gesture_text = "—"
            info_lines = []
            best_conf = 0.0
            primary_fingers = [False] * 5

            if num_hands > 0:
                for hi, hand_lms in enumerate(result.hand_landmarks):
                    handedness = ""
                    conf = 0.0
                    if result.handedness and hi < len(result.handedness):
                        cats = result.handedness[hi]
                        if cats:
                            handedness = cats[0].category_name
                            conf = cats[0].score

                    if self.show_landmarks:
                        draw_hand(frame, hand_lms, w, h, handedness)

                    gesture = detect_gesture(hand_lms)
                    fingers_up = get_fingers_up(hand_lms)

                    if hi == 0:
                        gesture_text = gesture
                        best_conf = conf
                        primary_fingers = fingers_up

                    info_lines.append(f"Hand {hi+1}: {handedness or '?'}  ({conf*100:.0f}%)")
                    info_lines.append(f"  → {gesture}")
                    info_lines.append(f"  → {sum(fingers_up)}/5 fingers up")

                    x_coords = [lm.x for lm in hand_lms]
                    y_coords = [lm.y for lm in hand_lms]
                    cx = int((min(x_coords) + max(x_coords)) / 2 * w)
                    cy = int((min(y_coords) + max(y_coords)) / 2 * h) - 15
                    cv2.putText(frame, gesture, (cx - 50, cy),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2, cv2.LINE_AA)

                    if gesture != last_gesture and gesture_cooldown <= 0:
                        ts = time.strftime("%H:%M:%S")
                        entry = f"[{ts}] {handedness}: {gesture}"
                        self.root.after(0, lambda e=entry: self.append_log(self.gesture_log, e))
                        last_gesture = gesture
                        gesture_cooldown = 8
                    gesture_cooldown -= 1

                    pos_desc = describe_position(fingers_up)
                    if pos_desc != last_position and position_cooldown <= 0:
                        ts = time.strftime("%H:%M:%S")
                        entry = f"[{ts}] {handedness}: {pos_desc}"
                        self.root.after(0, lambda e=entry: self.append_log(self.position_log, e))
                        last_position = pos_desc
                        position_cooldown = 8
                    position_cooldown -= 1
            else:
                info_lines.append("No hand detected")
                last_gesture = ""
                last_position = ""

            cv2.rectangle(frame, (0, 0), (w, 36), (0, 0, 0), -1)
            cv2.putText(frame, f"Gesture: {gesture_text}", (10, 26),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 212, 170), 2, cv2.LINE_AA)
            cv2.putText(frame, f"Hands: {num_hands}", (w - 130, 26),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2, cv2.LINE_AA)
            cv2.putText(frame, f"FPS: {self.fps:.0f}", (w - 260, 26),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2, cv2.LINE_AA)

            if self.recording and self.writer is not None:
                cv2.circle(frame, (w - 15, 18), 6, (0, 0, 255), -1)
                self.writer.write(frame)

            now = time.time()
            dt = now - self._prev_time
            self._prev_time = now
            self._frame_times.append(dt)
            if len(self._frame_times) > 30:
                self._frame_times.pop(0)
            if self._frame_times:
                avg_dt = sum(self._frame_times) / len(self._frame_times)
                self.fps = 1.0 / avg_dt if avg_dt > 0 else 0.0

            self._last_frame = frame.copy()

            self.gesture_var.set(gesture_text)
            self.hands_var.set(str(num_hands))
            self.fps_var.set(f"{self.fps:.0f}")
            self.conf_var.set(f"{best_conf*100:.0f}%")
            self.info_var.set("\n".join(info_lines) if info_lines else "No hand detected")

            for i, (dot, sv) in enumerate(self.finger_vars):
                if num_hands > 0 and primary_fingers[i]:
                    dot.config(fg=ACCENT)
                    sv.set("UP")
                elif num_hands > 0:
                    dot.config(fg=DANGER)
                    sv.set("down")
                else:
                    dot.config(fg=TEXT_DIM)
                    sv.set("—")

            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            img = ImageTk.PhotoImage(img)
            self.video_label.img = img
            self.video_label.config(image=img)

        self._cleanup_camera()

    def stop(self):
        self.running = False

    def _cleanup_camera(self):
        if self.recording and self.writer is not None:
            self.writer.release()
            self.writer = None
            self.recording = False
            self.record_btn.config(text="●  Record")
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        if self.landmarker is not None:
            self.landmarker.close()
            self.landmarker = None
        self.video_label.config(image="")
        self.gesture_var.set("—")
        self.hands_var.set("0")
        self.fps_var.set("0")
        self.conf_var.set("0%")
        self.info_var.set("No hand detected")
        for dot, sv in self.finger_vars:
            dot.config(fg=TEXT_DIM)
            sv.set("—")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.snapshot_btn.config(state=tk.DISABLED)
        self.record_btn.config(state=tk.DISABLED)
        self.status_var.set("Stopped")

    def on_exit(self):
        self.running = False
        if self.recording and self.writer is not None:
            self.writer.release()
        if self.cap is not None:
            self.cap.release()
        if self.landmarker is not None:
            self.landmarker.close()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = HandDetectionApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_exit)
    root.mainloop()