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

FACE_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
FACE_MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "face_landmarker.task")

from mediapipe.tasks.python import vision

FC = vision.FaceLandmarksConnections

CONTOUR_SETS = {
    "Face Oval": (FC.FACE_LANDMARKS_FACE_OVAL, (100, 100, 100)),
    "Left Eye": (FC.FACE_LANDMARKS_LEFT_EYE, (0, 220, 255)),
    "Right Eye": (FC.FACE_LANDMARKS_RIGHT_EYE, (0, 220, 255)),
    "Left Brow": (FC.FACE_LANDMARKS_LEFT_EYEBROW, (255, 180, 60)),
    "Right Brow": (FC.FACE_LANDMARKS_RIGHT_EYEBROW, (255, 180, 60)),
    "Lips": (FC.FACE_LANDMARKS_LIPS, (255, 80, 120)),
    "Left Iris": (FC.FACE_LANDMARKS_LEFT_IRIS, (80, 255, 120)),
    "Right Iris": (FC.FACE_LANDMARKS_RIGHT_IRIS, (80, 255, 120)),
    "Nose": (FC.FACE_LANDMARKS_NOSE, (200, 200, 255)),
}

BLENDSHAKE_KEYS = [
    "eyeBlinkLeft", "eyeBlinkRight",
    "eyeLookUpLeft", "eyeLookUpRight",
    "eyeLookDownLeft", "eyeLookDownRight",
    "eyebrowUpLeft", "eyebrowUpRight",
    "jawOpen",
    "mouthSmileLeft", "mouthSmileRight",
    "mouthFrownLeft", "mouthFrownRight",
    "mouthPucker", "mouthLeft", "mouthRight",
    "noseSneerLeft", "noseSneerRight",
    "cheekSquintLeft", "cheekSquintRight",
    "eyeSquintLeft", "eyeSquintRight",
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


def ensure_model(url, path):
    if os.path.exists(path):
        return True
    try:
        urllib.request.urlretrieve(url, path)
        return True
    except Exception as e:
        print(f"Failed to download model: {e}")
        return False


def get_blendshape_dict(blendshapes_list):
    result = {}
    if not blendshapes_list:
        return result
    for cat in blendshapes_list:
        result[cat.category_name] = cat.score
    return result


def estimate_head_pose(landmarks):
    if len(landmarks) < 234:
        return "Head: facing forward"
    nose = landmarks[1]
    left_eye = landmarks[33]
    right_eye = landmarks[263]
    left_face = landmarks[234]
    right_face = landmarks[454]
    forehead = landmarks[10]
    chin = landmarks[152]

    eye_mid_x = (left_eye.x + right_eye.x) / 2
    face_mid_x = (left_face.x + right_face.x) / 2
    yaw = nose.x - face_mid_x

    nose_to_forehead = forehead.y - nose.y
    nose_to_chin = chin.y - nose.y
    if nose_to_chin > 0.001:
        pitch_ratio = nose_to_forehead / nose_to_chin
    else:
        pitch_ratio = 1.0

    roll = left_eye.y - right_eye.y

    parts = []

    if yaw > 0.04:
        parts.append("Head turned right")
    elif yaw < -0.04:
        parts.append("Head turned left")
    else:
        parts.append("Head facing forward")

    if pitch_ratio > 1.3:
        parts.append("head tilted up")
    elif pitch_ratio < 0.6:
        parts.append("head tilted down")
    else:
        parts.append("head level")

    if roll > 0.02:
        parts.append("head rolled right")
    elif roll < -0.02:
        parts.append("head rolled left")

    return "  |  ".join(parts)


def detect_expression(bs, landmarks=None):
    expressions = []

    left_blink = bs.get("eyeBlinkLeft", 0)
    right_blink = bs.get("eyeBlinkRight", 0)
    avg_blink = (left_blink + right_blink) / 2

    smile_l = bs.get("mouthSmileLeft", 0)
    smile_r = bs.get("mouthSmileRight", 0)
    avg_smile = (smile_l + smile_r) / 2
    smile_asym = smile_l - smile_r

    jaw = bs.get("jawOpen", 0)

    brow_l = bs.get("eyebrowUpLeft", 0)
    brow_r = bs.get("eyebrowUpRight", 0)
    avg_brow = (brow_l + brow_r) / 2
    brow_asym = brow_l - brow_r

    brow_down_l = bs.get("eyebrowDownLeft", 0)
    brow_down_r = bs.get("eyebrowDownRight", 0)
    avg_brow_down = (brow_down_l + brow_down_r) / 2

    frown_l = bs.get("mouthFrownLeft", 0)
    frown_r = bs.get("mouthFrownRight", 0)
    avg_frown = (frown_l + frown_r) / 2

    pucker = bs.get("mouthPucker", 0)
    squint_l = bs.get("eyeSquintLeft", 0)
    squint_r = bs.get("eyeSquintRight", 0)
    avg_squint = (squint_l + squint_r) / 2

    sneer_l = bs.get("noseSneerLeft", 0)
    sneer_r = bs.get("noseSneerRight", 0)

    look_up_l = bs.get("eyeLookUpLeft", 0)
    look_up_r = bs.get("eyeLookUpRight", 0)
    look_dn_l = bs.get("eyeLookDownLeft", 0)
    look_dn_r = bs.get("eyeLookDownRight", 0)
    look_out_l = bs.get("eyeLookOutLeft", 0)
    look_in_l = bs.get("eyeLookInLeft", 0)
    look_out_r = bs.get("eyeLookOutRight", 0)
    look_in_r = bs.get("eyeLookInRight", 0)

    cheek_l = bs.get("cheekSquintLeft", 0)
    cheek_r = bs.get("cheekSquintRight", 0)

    mouth_left = bs.get("mouthLeft", 0)
    mouth_right = bs.get("mouthRight", 0)
    mouth_shrug = bs.get("mouthShrugLower", 0)
    mouth_press = bs.get("mouthPressLeft", 0) + bs.get("mouthPressRight", 0)
    mouth_stretch = bs.get("mouthStretchLeft", 0) + bs.get("mouthStretchRight", 0)
    mouth_upper = bs.get("mouthFunnel", 0)
    tongue = bs.get("tongueOut", 0)

    if avg_blink > 0.6:
        expressions.append("Eyes Closed (Blinking)")
    elif left_blink > 0.5 and right_blink < 0.3:
        expressions.append("Left Wink")
    elif right_blink > 0.5 and left_blink < 0.3:
        expressions.append("Right Wink")
    elif avg_blink > 0.3:
        expressions.append("Eyes Half Closed")
    else:
        if avg_squint > 0.5:
            expressions.append("Squinting")
        elif avg_squint > 0.25:
            expressions.append("E Narrowed")
        else:
            expressions.append("Eyes Open")

    gaze_h = (look_out_l + look_in_r) - (look_in_l + look_out_r)
    gaze_v = (look_up_l + look_up_r) - (look_dn_l + look_dn_r)
    if abs(gaze_h) > 0.3 or abs(gaze_v) > 0.3:
        if gaze_h > 0.3:
            expressions.append("Looking Right")
        elif gaze_h < -0.3:
            expressions.append("Looking Left")
        if gaze_v > 0.3:
            expressions.append("Looking Up")
        elif gaze_v < -0.3:
            expressions.append("Looking Down")
    else:
        expressions.append("Gaze Center")

    if avg_brow > 0.5:
        expressions.append("Brows Raised High")
    elif avg_brow > 0.25:
        expressions.append("Brows Raised")
    elif avg_brow_down > 0.3:
        expressions.append("Brows Furrowed")
    else:
        expressions.append("Brows Relaxed")

    if abs(brow_asym) > 0.2:
        expressions.append("Brow Asymmetric")

    if avg_smile > 0.6:
        expressions.append("Big Smile")
    elif avg_smile > 0.3:
        expressions.append("Smiling")
    elif avg_frown > 0.4:
        expressions.append("Frowning")
    elif avg_frown > 0.2:
        expressions.append("Slight Frown")

    if abs(smile_asym) > 0.25:
        if smile_asym > 0:
            expressions.append("Smirk (Left)")
        else:
            expressions.append("Smirk (Right)")

    if jaw > 0.6:
        expressions.append("Mouth Wide Open")
    elif jaw > 0.3:
        expressions.append("Mouth Open")
    elif jaw > 0.1:
        expressions.append("Mouth Slightly Open")
    else:
        expressions.append("Mouth Closed")

    if pucker > 0.4:
        expressions.append("Puckering / Kissing")
    if mouth_press > 0.5:
        expressions.append("Lips Pressed")
    if mouth_stretch > 0.5:
        expressions.append("Mouth Stretched")
    if mouth_upper > 0.4:
        expressions.append("Lips Funneled")
    if mouth_shrug > 0.3:
        expressions.append("Mouth Shrugging")
    if tongue > 0.3:
        expressions.append("Tongue Out")

    if mouth_left > 0.3 and mouth_right < 0.1:
        expressions.append("Mouth Shifted Left")
    elif mouth_right > 0.3 and mouth_left < 0.1:
        expressions.append("Mouth Shifted Right")

    if sneer_l > 0.4 or sneer_r > 0.4:
        if sneer_l > sneer_r:
            expressions.append("Sneer (Left)")
        else:
            expressions.append("Sneer (Right)")

    if cheek_l > 0.4 or cheek_r > 0.4:
        expressions.append("Cheeks Raised")

    if landmarks is not None:
        head_pose = estimate_head_pose(landmarks)
        for hp in head_pose.split("  |  "):
            expressions.append(hp)

    return expressions


def describe_face_state(bs, landmarks=None):
    parts = []

    left_blink = bs.get("eyeBlinkLeft", 0)
    right_blink = bs.get("eyeBlinkRight", 0)

    def eye_state(blink):
        if blink > 0.6:
            return "closed"
        elif blink > 0.3:
            return "half-closed"
        else:
            return "open"

    parts.append(f"L eye: {eye_state(left_blink)}")
    parts.append(f"R eye: {eye_state(right_blink)}")

    look_up = bs.get("eyeLookUpLeft", 0) + bs.get("eyeLookUpRight", 0)
    look_dn = bs.get("eyeLookDownLeft", 0) + bs.get("eyeLookDownRight", 0)
    look_l = bs.get("eyeLookOutLeft", 0) + bs.get("eyeLookInRight", 0)
    look_r = bs.get("eyeLookInLeft", 0) + bs.get("eyeLookOutRight", 0)
    if look_up > look_dn and look_up > look_l and look_up > look_r and look_up > 0.4:
        parts.append("gaze: up")
    elif look_dn > 0.4 and look_dn >= look_up and look_dn >= look_l and look_dn >= look_r:
        parts.append("gaze: down")
    elif look_l > 0.4 and look_l >= look_r:
        parts.append("gaze: left")
    elif look_r > 0.4:
        parts.append("gaze: right")
    else:
        parts.append("gaze: center")

    jaw = bs.get("jawOpen", 0)
    if jaw > 0.6:
        parts.append("mouth: wide open")
    elif jaw > 0.3:
        parts.append("mouth: open")
    elif jaw > 0.1:
        parts.append("mouth: slightly open")
    else:
        parts.append("mouth: closed")

    smile_l = bs.get("mouthSmileLeft", 0)
    smile_r = bs.get("mouthSmileRight", 0)
    avg_smile = (smile_l + smile_r) / 2
    frown_l = bs.get("mouthFrownLeft", 0)
    frown_r = bs.get("mouthFrownRight", 0)
    avg_frown = (frown_l + frown_r) / 2
    if avg_smile > 0.4:
        parts.append("smile: yes")
    elif avg_frown > 0.3:
        parts.append("smile: no (frowning)")
    else:
        parts.append("smile: no")

    pucker = bs.get("mouthPucker", 0)
    if pucker > 0.4:
        parts.append("lips: puckered")
    else:
        parts.append("lips: normal")

    brow_l = bs.get("eyebrowUpLeft", 0)
    brow_r = bs.get("eyebrowUpRight", 0)
    avg_brow = (brow_l + brow_r) / 2
    brow_dn = (bs.get("eyebrowDownLeft", 0) + bs.get("eyebrowDownRight", 0)) / 2
    if avg_brow > 0.3:
        parts.append("brows: raised")
    elif brow_dn > 0.3:
        parts.append("brows: furrowed")
    else:
        parts.append("brows: relaxed")

    if abs(brow_l - brow_r) > 0.2:
        parts.append("brows: asymmetric")

    squint = (bs.get("eyeSquintLeft", 0) + bs.get("eyeSquintRight", 0)) / 2
    if squint > 0.4:
        parts.append("eyes: squinting")

    if bs.get("noseSneerLeft", 0) > 0.4 or bs.get("noseSneerRight", 0) > 0.4:
        parts.append("nose: sneering")

    if bs.get("tongueOut", 0) > 0.3:
        parts.append("tongue: out")

    if landmarks is not None:
        parts.append(estimate_head_pose(landmarks))

    return "  |  ".join(parts)


def draw_face(frame, landmarks, w, h, draw_tess=False):
    pts = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]

    if draw_tess:
        for conn in FC.FACE_LANDMARKS_TESSELATION:
            cv2.line(frame, pts[conn.start], pts[conn.end], (40, 40, 50), 1)

    for name, (conns, color) in CONTOUR_SETS.items():
        for conn in conns:
            cv2.line(frame, pts[conn.start], pts[conn.end], color, 2)

    for idx in [468, 473]:
        if idx < len(pts):
            cv2.circle(frame, pts[idx], 4, (80, 255, 120), -1)


class FaceDetectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Detection  ·  MediaPipe + OpenCV")
        self.root.geometry("1180x760")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_DARK)

        self.running = False
        self.cap = None
        self.landmarker = None
        self.mirror = True
        self.show_mesh = True
        self.show_tess = False
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
        style.configure(".", background=BG_DARK, foreground=TEXT_PRIMARY, font=("Segoe UI", 10))
        style.configure("TFrame", background=BG_DARK)
        style.configure("Panel.TFrame", background=BG_PANEL)
        style.configure("Card.TFrame", background=BG_CARD)
        style.configure("TLabel", background=BG_DARK, foreground=TEXT_PRIMARY)
        style.configure("Panel.TLabel", background=BG_PANEL, foreground=TEXT_PRIMARY)
        style.configure("Card.TLabel", background=BG_CARD, foreground=TEXT_PRIMARY)
        style.configure("Dim.TLabel", background=BG_PANEL, foreground=TEXT_DIM, font=("Segoe UI", 9))
        style.configure("Title.TLabel", background=BG_DARK, foreground=ACCENT, font=("Segoe UI", 16, "bold"))
        style.configure("Subtitle.TLabel", background=BG_DARK, foreground=TEXT_SECONDARY, font=("Segoe UI", 9))
        style.configure("Gesture.TLabel", background=BG_CARD, foreground=ACCENT, font=("Segoe UI", 18, "bold"))
        style.configure("StatVal.TLabel", background=BG_CARD, foreground=ACCENT2, font=("Segoe UI", 14, "bold"))
        style.configure("Accent.TButton", background=ACCENT, foreground="#0a0a0a", font=("Segoe UI", 10, "bold"), borderwidth=0, padding=8)
        style.map("Accent.TButton", background=[("active", "#00b894"), ("disabled", "#2a2d3a")], foreground=[("disabled", TEXT_DIM)])
        style.configure("Danger.TButton", background=DANGER, foreground="#ffffff", font=("Segoe UI", 10, "bold"), borderwidth=0, padding=8)
        style.map("Danger.TButton", background=[("active", "#e04856")])
        style.configure("Toggle.TButton", background=BG_CARD, foreground=TEXT_PRIMARY, font=("Segoe UI", 9), borderwidth=0, padding=6)
        style.map("Toggle.TButton", background=[("active", "#2d3142")], foreground=[("active", ACCENT)])

    def _build_ui(self):
        header = ttk.Frame(self.root, style="Panel.TFrame")
        header.pack(fill=tk.X)
        ttk.Label(header, text="  😀  Face Detection & Expression Recognition",
                  style="Title.TLabel").pack(side=tk.LEFT, padx=12, pady=10)
        ttk.Label(header, text="MediaPipe Face Landmarker  ·  468 landmarks  ·  Blendshapes",
                  style="Subtitle.TLabel").pack(side=tk.LEFT, padx=4, pady=10)

        controls = ttk.Frame(self.root, style="Panel.TFrame")
        controls.pack(fill=tk.X, padx=10, pady=(8, 4))

        self.start_btn = ttk.Button(controls, text="▶  Start", style="Accent.TButton", command=self.start)
        self.start_btn.pack(side=tk.LEFT, padx=4, pady=8)
        self.stop_btn = ttk.Button(controls, text="■  Stop", style="Danger.TButton", command=self.stop, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=4, pady=8)
        self.snapshot_btn = ttk.Button(controls, text="📷  Snapshot", style="Toggle.TButton", command=self.save_snapshot, state=tk.DISABLED)
        self.snapshot_btn.pack(side=tk.LEFT, padx=4, pady=8)
        self.record_btn = ttk.Button(controls, text="●  Record", style="Toggle.TButton", command=self.toggle_record, state=tk.DISABLED)
        self.record_btn.pack(side=tk.LEFT, padx=4, pady=8)
        self.mirror_btn = ttk.Button(controls, text="🪞  Mirror: ON", style="Toggle.TButton", command=self.toggle_mirror)
        self.mirror_btn.pack(side=tk.LEFT, padx=4, pady=8)
        self.mesh_btn = ttk.Button(controls, text="👁  Mesh: ON", style="Toggle.TButton", command=self.toggle_mesh)
        self.mesh_btn.pack(side=tk.LEFT, padx=4, pady=8)
        self.tess_btn = ttk.Button(controls, text="🕸  Tessellation: OFF", style="Toggle.TButton", command=self.toggle_tess)
        self.tess_btn.pack(side=tk.LEFT, padx=4, pady=8)
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
        ttk.Label(gesture_card, text="EXPRESSION", style="Dim.TLabel").pack(anchor=tk.W)
        self.expr_var = tk.StringVar(value="—")
        ttk.Label(gesture_card, textvariable=self.expr_var, style="Gesture.TLabel").pack(anchor=tk.W, pady=(4, 0))

        stats_card = ttk.Frame(sidebar, style="Card.TFrame", padding=12)
        stats_card.pack(fill=tk.X, padx=8, pady=4)
        ttk.Label(stats_card, text="LIVE STATS", style="Dim.TLabel").pack(anchor=tk.W)
        stats_row = ttk.Frame(stats_card, style="Card.TFrame")
        stats_row.pack(fill=tk.X, pady=(6, 0))
        for col, (label, var_attr) in enumerate([("FPS", "fps_var"), ("Faces", "faces_var"), ("Conf.", "conf_var")]):
            cell = ttk.Frame(stats_row, style="Card.TFrame")
            cell.grid(row=0, column=col, sticky="nsew", padx=2)
            stats_row.grid_columnconfigure(col, weight=1)
            setattr(self, var_attr, tk.StringVar(value="0"))
            ttk.Label(cell, text=label, style="Dim.TLabel").pack(anchor=tk.W)
            ttk.Label(cell, textvariable=getattr(self, var_attr), style="StatVal.TLabel").pack(anchor=tk.W)

        info_card = ttk.Frame(sidebar, style="Card.TFrame", padding=12)
        info_card.pack(fill=tk.X, padx=8, pady=4)
        ttk.Label(info_card, text="FACE DETAILS", style="Dim.TLabel").pack(anchor=tk.W)
        self.info_var = tk.StringVar(value="No face detected")
        ttk.Label(info_card, textvariable=self.info_var, style="Card.TLabel", justify=tk.LEFT, font=("Segoe UI", 9)).pack(anchor=tk.W, pady=(4, 0))

        metric_card = ttk.Frame(sidebar, style="Card.TFrame", padding=12)
        metric_card.pack(fill=tk.X, padx=8, pady=4)
        ttk.Label(metric_card, text="EXPRESSION METRICS", style="Dim.TLabel").pack(anchor=tk.W)
        self.metric_vars = []
        metric_names = ["Smile", "Jaw Open", "Blink L", "Blink R", "Brow Up", "Squint", "Pucker", "Frown"]
        mg = ttk.Frame(metric_card, style="Card.TFrame")
        mg.pack(fill=tk.X, pady=(4, 0))
        for i, name in enumerate(metric_names):
            r, c = divmod(i, 2)
            cell = ttk.Frame(mg, style="Card.TFrame")
            cell.grid(row=r, column=c, sticky="ew", padx=2, pady=1)
            mg.grid_columnconfigure(c, weight=1)
            ttk.Label(cell, text=name, style="Dim.TLabel", font=("Segoe UI", 8)).pack(side=tk.LEFT)
            sv = tk.StringVar(value="0%")
            ttk.Label(cell, textvariable=sv, style="Card.TLabel", font=("Segoe UI", 8, "bold"), foreground=ACCENT2).pack(side=tk.RIGHT)
            self.metric_vars.append((name, sv))

        log_card = ttk.Frame(sidebar, style="Card.TFrame", padding=10)
        log_card.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        ttk.Label(log_card, text="EXPRESSION LOG", style="Dim.TLabel").pack(anchor=tk.W)
        self.expr_log = tk.Text(log_card, height=5, font=("Consolas", 8), bg="#16181f", fg=ACCENT, borderwidth=0, padx=6, pady=4, state=tk.DISABLED)
        self.expr_log.pack(fill=tk.BOTH, expand=True, pady=(4, 6))
        ttk.Label(log_card, text="FACE STATE LOG", style="Dim.TLabel").pack(anchor=tk.W)
        self.state_log = tk.Text(log_card, height=5, font=("Consolas", 8), bg="#16181f", fg=ACCENT2, borderwidth=0, padx=6, pady=4, state=tk.DISABLED)
        self.state_log.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

        footer = ttk.Frame(self.root, style="Panel.TFrame")
        footer.pack(fill=tk.X, padx=10, pady=(4, 8))
        self.status_var = tk.StringVar(value="Ready — click Start to begin")
        ttk.Label(footer, textvariable=self.status_var, style="Panel.TLabel", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=10, pady=6)
        ttk.Label(footer, text="468 landmarks  ·  blendshapes  ·  up to 2 faces", style="Dim.TLabel").pack(side=tk.RIGHT, padx=10, pady=6)

    def toggle_mirror(self):
        self.mirror = not self.mirror
        self.mirror_btn.config(text=f"🪞  Mirror: {'ON' if self.mirror else 'OFF'}")

    def toggle_mesh(self):
        self.show_mesh = not self.show_mesh
        self.mesh_btn.config(text=f"👁  Mesh: {'ON' if self.show_mesh else 'OFF'}")

    def toggle_tess(self):
        self.show_tess = not self.show_tess
        self.tess_btn.config(text=f"🕸  Tessellation: {'ON' if self.show_tess else 'OFF'}")

    def toggle_record(self):
        if not self.running:
            return
        if not self.recording:
            path = filedialog.asksaveasfilename(defaultextension=".avi", filetypes=[("AVI Video", "*.avi")], initialfile="face_record.avi")
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
        for w in (self.expr_log, self.state_log):
            w.config(state=tk.NORMAL)
            w.delete(1.0, tk.END)
            w.config(state=tk.DISABLED)

    def append_log(self, widget, text):
        widget.config(state=tk.NORMAL)
        widget.insert(tk.END, text + "\n")
        widget.see(tk.END)
        widget.config(state=tk.DISABLED)

    def save_snapshot(self):
        if self._last_frame is None:
            return
        filename = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg")], initialfile=f"face_snapshot_{self.snapshot_count:03d}.png")
        if filename:
            cv2.imwrite(filename, self._last_frame)
            self.snapshot_count += 1
            self.status_var.set(f"Snapshot saved: {filename}")

    def start(self):
        if self.running:
            return
        if not ensure_model(FACE_MODEL_URL, FACE_MODEL_PATH):
            messagebox.showerror("Error", f"Could not download model to:\n{FACE_MODEL_PATH}\nDownload manually from:\n{FACE_MODEL_URL}")
            return
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Could not open webcam.")
            self.cap = None
            return
        options = vision.FaceLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=FACE_MODEL_PATH),
            running_mode=vision.RunningMode.VIDEO,
            num_faces=2,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5,
            output_face_blendshapes=True,
            output_facial_transformation_matrixes=False,
        )
        self.landmarker = vision.FaceLandmarker.create_from_options(options)
        self.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.snapshot_btn.config(state=tk.NORMAL)
        self.record_btn.config(state=tk.NORMAL)
        self.status_var.set("Running — look at the webcam")
        self._prev_time = time.time()
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        timestamp = 0
        last_expr = ""
        last_state = ""
        expr_cd = 0
        state_cd = 0

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

            num_faces = len(result.face_landmarks) if result.face_landmarks else 0
            expr_text = "—"
            info_lines = []
            best_conf = 0.0
            primary_bs = {}

            if num_faces > 0:
                for fi, face_lms in enumerate(result.face_landmarks):
                    if self.show_mesh:
                        draw_face(frame, face_lms, w, h, draw_tess=self.show_tess)

                    bs = {}
                    if result.face_blendshapes and fi < len(result.face_blendshapes):
                        bs = get_blendshape_dict(result.face_blendshapes[fi])

                    expressions = detect_expression(bs, face_lms)
                    expr_str = ", ".join(expressions)

                    if fi == 0:
                        expr_text = expr_str
                        primary_bs = bs
                        best_conf = 1.0 - bs.get("eyeBlinkLeft", 0) * 0.1

                    info_lines.append(f"Face {fi+1}: {len(face_lms)} landmarks")
                    info_lines.append(f"  → {expr_str}")

                    x_coords = [lm.x for lm in face_lms]
                    y_coords = [lm.y for lm in face_lms]
                    cx = int((min(x_coords) + max(x_coords)) / 2 * w)
                    cy = int(min(y_coords) * h) - 10
                    label_lines = expr_str.split(", ")
                    for li, line in enumerate(label_lines[:4]):
                        cv2.putText(frame, line, (cx - 80, max(cy, 20) + li * 22),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)

                    if expr_str != last_expr and expr_cd <= 0:
                        ts = time.strftime("%H:%M:%S")
                        entry = f"[{ts}] Face {fi+1}: {expr_str}"
                        self.root.after(0, lambda e=entry: self.append_log(self.expr_log, e))
                        last_expr = expr_str
                        expr_cd = 8
                    expr_cd -= 1

                    state_desc = describe_face_state(bs, face_lms)
                    if state_desc != last_state and state_cd <= 0:
                        ts = time.strftime("%H:%M:%S")
                        entry = f"[{ts}] F{fi+1}: {state_desc}"
                        self.root.after(0, lambda e=entry: self.append_log(self.state_log, e))
                        last_state = state_desc
                        state_cd = 8
                    state_cd -= 1
            else:
                info_lines.append("No face detected")
                last_expr = ""
                last_state = ""

            cv2.rectangle(frame, (0, 0), (w, 36), (0, 0, 0), -1)
            short_expr = expr_text[:60] + "..." if len(expr_text) > 60 else expr_text
            cv2.putText(frame, short_expr, (10, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 212, 170), 2, cv2.LINE_AA)
            cv2.putText(frame, f"Faces: {num_faces}", (w - 130, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2, cv2.LINE_AA)
            cv2.putText(frame, f"FPS: {self.fps:.0f}", (w - 260, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2, cv2.LINE_AA)

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
            self.expr_var.set(expr_text)
            self.faces_var.set(str(num_faces))
            self.fps_var.set(f"{self.fps:.0f}")
            self.conf_var.set(f"{best_conf*100:.0f}%")
            self.info_var.set("\n".join(info_lines) if info_lines else "No face detected")

            metric_map = {
                "Smile": (primary_bs.get("mouthSmileLeft", 0) + primary_bs.get("mouthSmileRight", 0)) / 2,
                "Jaw Open": primary_bs.get("jawOpen", 0),
                "Blink L": primary_bs.get("eyeBlinkLeft", 0),
                "Blink R": primary_bs.get("eyeBlinkRight", 0),
                "Brow Up": (primary_bs.get("eyebrowUpLeft", 0) + primary_bs.get("eyebrowUpRight", 0)) / 2,
                "Squint": (primary_bs.get("eyeSquintLeft", 0) + primary_bs.get("eyeSquintRight", 0)) / 2,
                "Pucker": primary_bs.get("mouthPucker", 0),
                "Frown": (primary_bs.get("mouthFrownLeft", 0) + primary_bs.get("mouthFrownRight", 0)) / 2,
            }
            for name, sv in self.metric_vars:
                val = metric_map.get(name, 0)
                sv.set(f"{val*100:.0f}%")

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
        self.expr_var.set("—")
        self.faces_var.set("0")
        self.fps_var.set("0")
        self.conf_var.set("0%")
        self.info_var.set("No face detected")
        for _, sv in self.metric_vars:
            sv.set("0%")
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
    app = FaceDetectionApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_exit)
    root.mainloop()