"""Configuration for the Construction Site Safety Monitoring System."""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.environ.get(
    "PPE_MODEL_PATH",
    os.path.join(BASE_DIR, "ppe_yolov8.pt"),
)

FALLBACK_MODEL = "yolov8n.pt"

CONFIDENCE_THRESHOLD = 0.45
IOU_THRESHOLD = 0.50

INFERENCE_IMG_SIZE = 640

PPE_CLASS_NAMES = {
    "person": ["person", "worker", "Person", "people"],
    "helmet": ["hardhat", "helmet", "Hardhat", "Helmet", "hard-hat"],
    "no_helmet": ["no-hardhat", "no-helmet", "NO-Hardhat", "No-Helmet", "head"],
    "vest": ["safety-vest", "vest", "Safety Vest", "Vest", "safety_vest"],
    "no_vest": ["no-safety-vest", "no-vest", "NO-Safety Vest", "No-Vest"],
}

COLORS = {
    "person": (0, 255, 0),
    "helmet": (0, 200, 0),
    "no_helmet": (0, 0, 255),
    "vest": (0, 200, 0),
    "no_vest": (0, 165, 255),
    "warning": (0, 0, 255),
    "safe": (0, 200, 0),
    "info": (255, 255, 0),
}

HEAD_REGION_RATIO = 0.25
TORSO_REGION_RATIO = 0.55

IOU_MATCH_THRESHOLD = 0.15
CENTER_MATCH_THRESHOLD = 0.30

ALERT_LOG_FILE = os.path.join(BASE_DIR, "safety_alerts.log")
ALERT_COOLDOWN_SECONDS = 5.0

ENABLE_AUDIO_ALERTS = True
ENABLE_LOG_ALERTS = True

WARN_NO_HELMET = "WARNING: Worker without helmet detected!"
WARN_NO_VEST = "WARNING: Worker without safety vest detected!"
WARN_NO_BOTH = "WARNING: Worker without helmet AND safety vest detected!"

INFO_HELMET_OK = "Helmet OK"
INFO_VEST_OK = "Vest OK"