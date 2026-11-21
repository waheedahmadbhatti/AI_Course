"""Configuration for the Crowd Monitoring System."""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.environ.get(
    "CROWD_MODEL_PATH",
    os.path.join(BASE_DIR, "crowd_yolov8.pt"),
)

FALLBACK_MODEL = "yolov8n.pt"

CONFIDENCE_THRESHOLD = 0.40
IOU_THRESHOLD = 0.50

INFERENCE_IMG_SIZE = 640

PERSON_CLASS_ID = 0
PERSON_CLASS_NAMES = ["person", "people", "worker", "pedestrian", "human"]

TRACKER_TYPE = "bytetrack"
TRACK_PERSIST = True

COUNTING_LINE_RATIO = 0.5
COUNTING_LINE_ORIENTATION = "horizontal"

CROWD_WARNING_THRESHOLD = 20
CROWD_DANGER_THRESHOLD = 40

COLORS = {
    "person": (0, 255, 0),
    "person_tracked": (0, 200, 255),
    "counting_line": (0, 255, 255),
    "entry": (0, 255, 0),
    "exit": (0, 0, 255),
    "warning": (0, 165, 255),
    "danger": (0, 0, 255),
    "safe": (0, 200, 0),
    "hud_bg": (0, 0, 0),
    "text": (255, 255, 255),
    "text_highlight": (0, 255, 255),
}

TRACK_HISTORY_LEN = 30
SHOW_TRACK_TRAILS = True
SHOW_COUNTING_LINE = True
SHOW_DIRECTION_ARROWS = True

STATS_LOG_FILE = os.path.join(BASE_DIR, "crowd_stats.log")
ENABLE_LOG = True

HUD_BG_ALPHA = 0.6

MIN_TRACK_FRAMES = 3