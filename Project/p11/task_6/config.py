"""Configuration for the Waste Detection & Classification System."""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.environ.get(
    "WASTE_MODEL_PATH",
    os.path.join(BASE_DIR, "waste_yolov8.pt"),
)

FALLBACK_MODEL = "yolov8n.pt"

CONFIDENCE_THRESHOLD = 0.40
IOU_THRESHOLD = 0.50

INFERENCE_IMG_SIZE = 640

WASTE_CATEGORIES = {
    "plastic": {
        "aliases": [
            "plastic", "plastic-bottle", "plastic-bag", "plastic-container",
            "pet", "plastic-cup", "plastic-wrap", "Plastic", "PLASTIC",
        ],
        "color": (0, 0, 255),
        "recyclable": True,
        "icon": "P",
    },
    "paper": {
        "aliases": [
            "paper", "paper-bag", "cardboard", "paper-cup", "newspaper",
            "magazine", "paper-board", "Paper", "PAPER", "carton",
        ],
        "color": (0, 165, 255),
        "recyclable": True,
        "icon": "PP",
    },
    "metal": {
        "aliases": [
            "metal", "aluminum", "aluminum-can", "steel", "tin", "metal-can",
            "iron", "Metal", "METAL", "can", "tin-can",
        ],
        "color": (0, 200, 200),
        "recyclable": True,
        "icon": "M",
    },
    "glass": {
        "aliases": [
            "glass", "glass-bottle", "glass-jar", "Glass", "GLASS",
            "broken-glass",
        ],
        "color": (255, 255, 0),
        "recyclable": True,
        "icon": "G",
    },
    "organic": {
        "aliases": [
            "organic", "food", "food-waste", "biodegradable", "compost",
            "Organic", "ORGANIC", "fruit", "vegetable",
        ],
        "color": (0, 128, 0),
        "recyclable": False,
        "icon": "O",
    },
    "other": {
        "aliases": [
            "other", "trash", "garbage", "waste", "general", "misc",
            "Other", "OTHER", "non-recyclable", "landfill",
        ],
        "color": (128, 128, 128),
        "recyclable": False,
        "icon": "X",
    },
}

DEFAULT_CATEGORY = "other"

HUD_BG_ALPHA = 0.55

STATS_LOG_FILE = os.path.join(BASE_DIR, "waste_stats.log")
ENABLE_LOG = True

CONVEYOR_LINE_COLOR = (200, 200, 200)
SHOW_CONVEYOR_GUIDE = True

CATEGORY_LABEL_FONT_SCALE = 0.6
CATEGORY_LABEL_THICKNESS = 2