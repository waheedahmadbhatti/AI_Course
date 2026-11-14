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

POSE_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
POSE_MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pose_landmarker_lite.task")

from mediapipe.tasks.python import vision

POSE_CONNECTIONS = vision.PoseLandmarksConnections.POSE_LANDMARKS

LM = vision.PoseLandmark

KEY_LANDMARKS = {
    "Nose": LM.NOSE.value,
    "L Eye": LM.LEFT_EYE.value,
    "R Eye": LM.RIGHT_EYE.value,
    "L Ear": LM.LEFT_EAR.value,
    "R Ear": LM.RIGHT_EAR.value,
    "L Shoulder": LM.LEFT_SHOULDER.value,
    "R Shoulder": LM.RIGHT_SHOULDER.value,
    "L Elbow": LM.LEFT_ELBOW.value,
    "R Elbow": LM.RIGHT_ELBOW.value,
    "L Wrist": LM.LEFT_WRIST.value,
    "R Wrist": LM.RIGHT_WRIST.value,
    "L Hip": LM.LEFT_HIP.value,
    "R Hip": LM.RIGHT_HIP.value,
    "L Knee": LM.LEFT_KNEE.value,
    "R Knee": LM.RIGHT_KNEE.value,
    "L Ankle": LM.LEFT_ANKLE.value,
    "R Ankle": LM.RIGHT_ANKLE.value,
}

BODY_PART_COLORS = {
    "head": (255, 200, 100),
    "torso": (100, 255, 200),
    "left_arm": (80, 220, 255),
    "right_arm": (255, 100, 200),
    "left_leg": (200, 200, 50),
    "right_leg": (50, 200, 200),
}

BG_DARK = "#0f1117"
BG_PANEL = "#1a1d27"
BG_CARD = "#222632"
ACCENT = "#00d4aa"
ACCENT2 = "#3b82f6"
TEXT_PRIMARY = "#e8eaf0"
TEXT_SECONDARY = "#9aa0b4"
TEXT_DIM = "#6b7185"
DANGER = "#ff5b6e"


def ensure_model(url, path):
    if os.path.exists(path):
        return True
    try:
        urllib.request.urlretrieve(url, path)
        return True
    except Exception as e:
        print(f"Failed to download model: {e}")
        return False


def dist(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def is_visible(lm):
    return lm.visibility > 0.3 if hasattr(lm, "visibility") else True


def draw_pose(frame, landmarks, w, h):
    pts = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]

    for conn in POSE_CONNECTIONS:
        if is_visible(landmarks[conn.start]) and is_visible(landmarks[conn.end]):
            cv2.line(frame, pts[conn.start], pts[conn.end], (100, 255, 200), 3)

    for idx, p in enumerate(pts):
        if is_visible(landmarks[idx]):
            if idx in [LM.LEFT_SHOULDER.value, LM.RIGHT_SHOULDER.value,
                       LM.LEFT_HIP.value, LM.RIGHT_HIP.value, LM.NOSE.value]:
                cv2.circle(frame, p, 7, (255, 200, 100), -1)
                cv2.circle(frame, p, 7, (255, 255, 255), 1)
            else:
                cv2.circle(frame, p, 5, (80, 220, 255), -1)


def detect_posture(lm):
    postures = []

    nose = lm[LM.NOSE.value]
    l_shoulder = lm[LM.LEFT_SHOULDER.value]
    r_shoulder = lm[LM.RIGHT_SHOULDER.value]
    l_hip = lm[LM.LEFT_HIP.value]
    r_hip = lm[LM.RIGHT_HIP.value]
    l_wrist = lm[LM.LEFT_WRIST.value]
    r_wrist = lm[LM.RIGHT_WRIST.value]
    l_elbow = lm[LM.LEFT_ELBOW.value]
    r_elbow = lm[LM.RIGHT_ELBOW.value]
    l_knee = lm[LM.LEFT_KNEE.value]
    r_knee = lm[LM.RIGHT_KNEE.value]
    l_ankle = lm[LM.LEFT_ANKLE.value]
    r_ankle = lm[LM.RIGHT_ANKLE.value]

    if not (is_visible(l_shoulder) and is_visible(r_shoulder)):
        return ["Partial body"]

    shoulder_mid_y = (l_shoulder.y + r_shoulder.y) / 2
    shoulder_dx = abs(l_shoulder.x - r_shoulder.x)
    shoulder_dy = abs(l_shoulder.y - r_shoulder.y)

    if is_visible(l_hip) and is_visible(r_hip):
        hip_mid_y = (l_hip.y + r_hip.y) / 2
        torso_height = hip_mid_y - shoulder_mid_y

        if torso_height > 0:
            if shoulder_dy / torso_height > 0.4:
                postures.append("Leaning Sideways")
            elif shoulder_mid_y < hip_mid_y * 0.6:
                postures.append("Standing Upright")
            else:
                postures.append("Sitting / Crouching")
        else:
            postures.append("Bending Forward")

        hip_mid_x = (l_hip.x + r_hip.x) / 2
        if nose.y > hip_mid_y:
            postures.append("Bending Down")
        if abs(nose.x - hip_mid_x) > 0.15:
            if nose.x > hip_mid_x:
                postures.append("Leaning Right")
            else:
                postures.append("Leaning Left")
    else:
        postures.append("Upper Body Only")

    if is_visible(l_wrist) and is_visible(r_wrist):
        if l_wrist.y < shoulder_mid_y and r_wrist.y < shoulder_mid_y:
            if l_wrist.y < l_shoulder.y - 0.15 and r_wrist.y < r_shoulder.y - 0.15:
                postures.append("Both Arms Up")
            else:
                postures.append("Arms Raised")
        elif l_wrist.y < shoulder_mid_y:
            postures.append("Left Arm Up")
        elif r_wrist.y < shoulder_mid_y:
            postures.append("Right Arm Up")

        if abs(l_wrist.x - r_wrist.x) < 0.08 and l_wrist.y < shoulder_mid_y:
            postures.append("Hands Together")

    if is_visible(l_wrist) and is_visible(l_hip):
        if l_wrist.y > l_hip.y:
            postures.append("Left Hand Down")
    if is_visible(r_wrist) and is_visible(r_hip):
        if r_wrist.y > r_hip.y:
            postures.append("Right Hand Down")

    if is_visible(l_knee) and is_visible(r_knee) and is_visible(l_ankle) and is_visible(r_ankle):
        knee_mid_y = (l_knee.y + r_knee.y) / 2
        ankle_mid_y = (l_ankle.y + r_ankle.y) / 2
        if knee_mid_y > shoulder_mid_y + 0.3 and abs(l_knee.y - r_knee.y) > 0.1:
            postures.append("Kneeling / Lunging")

    if not postures:
        postures.append("Neutral Pose")

    return postures


def describe_body_state(lm):
    parts = []

    def part_state(name, idx):
        lm_val = lm[idx]
        if is_visible(lm_val):
            return f"{name}: visible"
        return f"{name}: hidden"

    parts.append(part_state("Head", LM.NOSE.value))
    parts.append(part_state("L Arm", LM.LEFT_WRIST.value))
    parts.append(part_state("R Arm", LM.RIGHT_WRIST.value))
    parts.append(part_state("L Leg", LM.LEFT_ANKLE.value))
    parts.append(part_state("R Leg", LM.RIGHT_ANKLE.value))

    if is_visible(lm[LM.LEFT_SHOULDER.value]) and is_visible(lm[LM.RIGHT_SHOULDER.value]):
        tilt = lm[LM.LEFT_SHOULDER.value].y - lm[LM.RIGHT_SHOULDER.value].y
        if abs(tilt) < 0.05:
            parts.append("Shoulders: level")
        elif tilt > 0:
            parts.append("Shoulders: tilted right")
        else:
            parts.append("Shoulders: tilted left")

    if is_visible(lm[LM.LEFT_WRIST.value]) and is_visible(lm[LM.LEFT_SHOULDER.value]):
        if lm[LM.LEFT_WRIST.value].y < lm[LM.LEFT_SHOULDER.value].y:
            parts.append("L hand: above shoulder")
        else:
            parts.append("L hand: below shoulder")
    if is_visible(lm[LM.RIGHT_WRIST.value]) and is_visible(lm[LM.RIGHT_SHOULDER.value]):
        if lm[LM.RIGHT_WRIST.value].y < lm[LM.RIGHT_SHOULDER.value].y:
            parts.append("R hand: above shoulder")
        else:
            parts.append("R hand: below shoulder")

    return "  |  ".join(parts)


class PoseDetectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Full Body Pose Detection  ·  MediaPipe + OpenCV")
        self.root.geometry("1180x760")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_DARK)

        self.running = False
        self.cap = None
        self.landmarker = None
        self.mirror = True
        self.show_skeleton = True
        self.recording = False
        self.writer = None
        self.snapshot_count = 0
        self.fps = 0.0
        self._prev_time = 0.0
        self._frame_times = []
        self._last_frame = None
        self.video_source = 0
        self.video_path = None
        self.video_total_frames = 0
        self.video_current_frame = 0

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
        ttk.Label(header, text="  🧍  Full Body Pose Detection",
                  style="Title.TLabel").pack(side=tk.LEFT, padx=12, pady=10)
        ttk.Label(header, text="MediaPipe Pose Landmarker  ·  33 landmarks  ·  Posture Analysis",
                  style="Subtitle.TLabel").pack(side=tk.LEFT, padx=4, pady=10)

        controls = ttk.Frame(self.root, style="Panel.TFrame")
        controls.pack(fill=tk.X, padx=10, pady=(8, 4))

        self.start_btn = ttk.Button(controls, text="▶  Start Webcam", style="Accent.TButton", command=self.start)
        self.start_btn.pack(side=tk.LEFT, padx=4, pady=8)
        self.upload_btn = ttk.Button(controls, text="📁  Upload Video", style="Accent.TButton", command=self.upload_video)
        self.upload_btn.pack(side=tk.LEFT, padx=4, pady=8)
        self.stop_btn = ttk.Button(controls, text="■  Stop", style="Danger.TButton", command=self.stop, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=4, pady=8)
        self.snapshot_btn = ttk.Button(controls, text="📷  Snapshot", style="Toggle.TButton", command=self.save_snapshot, state=tk.DISABLED)
        self.snapshot_btn.pack(side=tk.LEFT, padx=4, pady=8)
        self.record_btn = ttk.Button(controls, text="●  Record", style="Toggle.TButton", command=self.toggle_record, state=tk.DISABLED)
        self.record_btn.pack(side=tk.LEFT, padx=4, pady=8)
        self.mirror_btn = ttk.Button(controls, text="🪞  Mirror: ON", style="Toggle.TButton", command=self.toggle_mirror)
        self.mirror_btn.pack(side=tk.LEFT, padx=4, pady=8)
        self.skeleton_btn = ttk.Button(controls, text="🦴  Skeleton: ON", style="Toggle.TButton", command=self.toggle_skeleton)
        self.skeleton_btn.pack(side=tk.LEFT, padx=4, pady=8)
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
        ttk.Label(gesture_card, text="POSTURE", style="Dim.TLabel").pack(anchor=tk.W)
        self.posture_var = tk.StringVar(value="—")
        ttk.Label(gesture_card, textvariable=self.posture_var, style="Gesture.TLabel").pack(anchor=tk.W, pady=(4, 0))

        stats_card = ttk.Frame(sidebar, style="Card.TFrame", padding=12)
        stats_card.pack(fill=tk.X, padx=8, pady=4)
        ttk.Label(stats_card, text="LIVE STATS", style="Dim.TLabel").pack(anchor=tk.W)
        stats_row = ttk.Frame(stats_card, style="Card.TFrame")
        stats_row.pack(fill=tk.X, pady=(6, 0))
        for col, (label, var_attr) in enumerate([("FPS", "fps_var"), ("Persons", "persons_var"), ("LMs", "lms_var")]):
            cell = ttk.Frame(stats_row, style="Card.TFrame")
            cell.grid(row=0, column=col, sticky="nsew", padx=2)
            stats_row.grid_columnconfigure(col, weight=1)
            setattr(self, var_attr, tk.StringVar(value="0"))
            ttk.Label(cell, text=label, style="Dim.TLabel").pack(anchor=tk.W)
            ttk.Label(cell, textvariable=getattr(self, var_attr), style="StatVal.TLabel").pack(anchor=tk.W)

        info_card = ttk.Frame(sidebar, style="Card.TFrame", padding=12)
        info_card.pack(fill=tk.X, padx=8, pady=4)
        ttk.Label(info_card, text="POSE DETAILS", style="Dim.TLabel").pack(anchor=tk.W)
        self.info_var = tk.StringVar(value="No person detected")
        ttk.Label(info_card, textvariable=self.info_var, style="Card.TLabel", justify=tk.LEFT, font=("Segoe UI", 9)).pack(anchor=tk.W, pady=(4, 0))

        body_card = ttk.Frame(sidebar, style="Card.TFrame", padding=12)
        body_card.pack(fill=tk.X, padx=8, pady=4)
        ttk.Label(body_card, text="KEY BODY PARTS", style="Dim.TLabel").pack(anchor=tk.W)
        self.body_vars = []
        bg_grid = ttk.Frame(body_card, style="Card.TFrame")
        bg_grid.pack(fill=tk.X, pady=(4, 0))
        for i, name in enumerate(list(KEY_LANDMARKS.keys())):
            r, c = divmod(i, 2)
            cell = ttk.Frame(bg_grid, style="Card.TFrame")
            cell.grid(row=r, column=c, sticky="ew", padx=2, pady=1)
            bg_grid.grid_columnconfigure(c, weight=1)
            dot = tk.Label(cell, text="●", fg=TEXT_DIM, bg=BG_CARD, font=("Segoe UI", 8))
            dot.pack(side=tk.LEFT, padx=(0, 4))
            ttk.Label(cell, text=name, style="Card.TLabel", font=("Segoe UI", 8)).pack(side=tk.LEFT)
            sv = tk.StringVar(value="—")
            ttk.Label(cell, textvariable=sv, style="Card.TLabel", font=("Segoe UI", 8, "bold")).pack(side=tk.RIGHT)
            self.body_vars.append((name, dot, sv))

        log_card = ttk.Frame(sidebar, style="Card.TFrame", padding=10)
        log_card.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        ttk.Label(log_card, text="POSTURE LOG", style="Dim.TLabel").pack(anchor=tk.W)
        self.posture_log = tk.Text(log_card, height=5, font=("Consolas", 8), bg="#16181f", fg=ACCENT, borderwidth=0, padx=6, pady=4, state=tk.DISABLED)
        self.posture_log.pack(fill=tk.BOTH, expand=True, pady=(4, 6))
        ttk.Label(log_card, text="BODY STATE LOG", style="Dim.TLabel").pack(anchor=tk.W)
        self.state_log = tk.Text(log_card, height=5, font=("Consolas", 8), bg="#16181f", fg=ACCENT2, borderwidth=0, padx=6, pady=4, state=tk.DISABLED)
        self.state_log.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

        footer = ttk.Frame(self.root, style="Panel.TFrame")
        footer.pack(fill=tk.X, padx=10, pady=(4, 8))
        self.status_var = tk.StringVar(value="Ready — click Start to begin")
        ttk.Label(footer, textvariable=self.status_var, style="Panel.TLabel", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=10, pady=6)
        ttk.Label(footer, text="33 landmarks  ·  posture analysis  ·  up to 2 persons", style="Dim.TLabel").pack(side=tk.RIGHT, padx=10, pady=6)

    def toggle_mirror(self):
        self.mirror = not self.mirror
        self.mirror_btn.config(text=f"🪞  Mirror: {'ON' if self.mirror else 'OFF'}")

    def toggle_skeleton(self):
        self.show_skeleton = not self.show_skeleton
        self.skeleton_btn.config(text=f"🦴  Skeleton: {'ON' if self.show_skeleton else 'OFF'}")

    def toggle_record(self):
        if not self.running:
            return
        if not self.recording:
            path = filedialog.asksaveasfilename(defaultextension=".avi", filetypes=[("AVI Video", "*.avi")], initialfile="pose_record.avi")
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
        for w in (self.posture_log, self.state_log):
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
        filename = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg")], initialfile=f"pose_snapshot_{self.snapshot_count:03d}.png")
        if filename:
            cv2.imwrite(filename, self._last_frame)
            self.snapshot_count += 1
            self.status_var.set(f"Snapshot saved: {filename}")

    def upload_video(self):
        if self.running:
            return
        path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[
                ("Video Files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm"),
                ("MP4", "*.mp4"),
                ("AVI", "*.avi"),
                ("All Files", "*.*"),
            ])
        if not path:
            return
        self.video_path = path
        self.video_source = path
        self._start_detection(is_video=True)

    def start(self):
        if self.running:
            return
        self.video_source = 0
        self.video_path = None
        self._start_detection(is_video=False)

    def _start_detection(self, is_video=False):
        if not ensure_model(POSE_MODEL_URL, POSE_MODEL_PATH):
            messagebox.showerror("Error", f"Could not download model to:\n{POSE_MODEL_PATH}\nDownload manually from:\n{POSE_MODEL_URL}")
            return
        self.cap = cv2.VideoCapture(self.video_source)
        if not self.cap.isOpened():
            source_name = self.video_path if is_video else "webcam"
            messagebox.showerror("Error", f"Could not open {source_name}.")
            self.cap = None
            return
        if is_video:
            self.video_total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.video_current_frame = 0
        else:
            self.video_total_frames = 0
            self.video_current_frame = 0
        options = vision.PoseLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=POSE_MODEL_PATH),
            running_mode=vision.RunningMode.VIDEO,
            num_poses=2,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
            output_segmentation_masks=False,
        )
        self.landmarker = vision.PoseLandmarker.create_from_options(options)
        self.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.upload_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.snapshot_btn.config(state=tk.NORMAL)
        self.record_btn.config(state=tk.NORMAL)
        if is_video:
            fname = os.path.basename(self.video_path)
            self.status_var.set(f"Processing video: {fname}")
        else:
            self.status_var.set("Running — stand in front of the webcam")
        self._prev_time = time.time()
        threading.Thread(target=self._loop, daemon=True, kwargs={"is_video": is_video}).start()

    def _loop(self, is_video=False):
        timestamp = 0
        last_posture = ""
        last_state = ""
        posture_cd = 0
        state_cd = 0

        while self.running and self.cap is not None:
            ret, frame = self.cap.read()
            if not ret:
                if is_video:
                    self.root.after(0, lambda: self.status_var.set("Video ended — click Stop to reset"))
                break
            if is_video:
                self.video_current_frame += 1
            if self.mirror:
                frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            timestamp += 1
            result = self.landmarker.detect_for_video(mp_image, timestamp)

            num_poses = len(result.pose_landmarks) if result.pose_landmarks else 0
            posture_text = "—"
            info_lines = []
            visible_count = 0
            primary_lm = []

            if num_poses > 0:
                for pi, pose_lms in enumerate(result.pose_landmarks):
                    if self.show_skeleton:
                        draw_pose(frame, pose_lms, w, h)

                    postures = detect_posture(pose_lms)
                    posture_str = ", ".join(postures)

                    if pi == 0:
                        posture_text = posture_str
                        primary_lm = pose_lms
                        visible_count = sum(1 for lm in pose_lms if is_visible(lm))

                    info_lines.append(f"Person {pi+1}: {visible_count if pi == 0 else sum(1 for lm in pose_lms if is_visible(lm))}/33 landmarks")
                    info_lines.append(f"  → {posture_str}")

                    x_coords = [lm.x for lm in pose_lms if is_visible(lm)]
                    y_coords = [lm.y for lm in pose_lms if is_visible(lm)]
                    if x_coords:
                        cx = int((min(x_coords) + max(x_coords)) / 2 * w)
                        cy = int(min(y_coords) * h) - 10
                        cv2.putText(frame, posture_str, (cx - 60, max(cy, 20)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2, cv2.LINE_AA)

                    if posture_str != last_posture and posture_cd <= 0:
                        ts = time.strftime("%H:%M:%S")
                        entry = f"[{ts}] Person {pi+1}: {posture_str}"
                        self.root.after(0, lambda e=entry: self.append_log(self.posture_log, e))
                        last_posture = posture_str
                        posture_cd = 8
                    posture_cd -= 1

                    state_desc = describe_body_state(pose_lms)
                    if state_desc != last_state and state_cd <= 0:
                        ts = time.strftime("%H:%M:%S")
                        entry = f"[{ts}] P{pi+1}: {state_desc}"
                        self.root.after(0, lambda e=entry: self.append_log(self.state_log, e))
                        last_state = state_desc
                        state_cd = 8
                    state_cd -= 1
            else:
                info_lines.append("No person detected")
                last_posture = ""
                last_state = ""

            cv2.rectangle(frame, (0, 0), (w, 36), (0, 0, 0), -1)
            cv2.putText(frame, f"Posture: {posture_text}", (10, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 212, 170), 2, cv2.LINE_AA)
            cv2.putText(frame, f"Persons: {num_poses}", (w - 140, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2, cv2.LINE_AA)
            cv2.putText(frame, f"FPS: {self.fps:.0f}", (w - 270, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2, cv2.LINE_AA)

            if is_video and self.video_total_frames > 0:
                progress = self.video_current_frame / self.video_total_frames
                bar_w = int(w * progress)
                cv2.rectangle(frame, (0, h - 6), (w, h), (40, 40, 50), -1)
                cv2.rectangle(frame, (0, h - 6), (bar_w, h), (0, 212, 170), -1)
                pct = int(progress * 100)
                cv2.putText(frame, f"{pct}%", (w - 50, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)

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
            self.posture_var.set(posture_text)
            self.persons_var.set(str(num_poses))
            self.fps_var.set(f"{self.fps:.0f}")
            self.lms_var.set(str(visible_count))
            self.info_var.set("\n".join(info_lines) if info_lines else "No person detected")

            for name, dot, sv in self.body_vars:
                idx = KEY_LANDMARKS[name]
                if primary_lm and is_visible(primary_lm[idx]):
                    dot.config(fg=ACCENT)
                    sv.set("vis")
                elif primary_lm:
                    dot.config(fg=DANGER)
                    sv.set("hidden")
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
        self.posture_var.set("—")
        self.persons_var.set("0")
        self.fps_var.set("0")
        self.lms_var.set("0")
        self.info_var.set("No person detected")
        for _, dot, sv in self.body_vars:
            dot.config(fg=TEXT_DIM)
            sv.set("—")
        self.start_btn.config(state=tk.NORMAL)
        self.upload_btn.config(state=tk.NORMAL)
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
    app = PoseDetectionApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_exit)
    root.mainloop()