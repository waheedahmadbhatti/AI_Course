"""Waste detector: runs YOLO inference and classifies waste items on a conveyor belt."""

from dataclasses import dataclass
from typing import List, Optional

import numpy as np
from ultralytics import YOLO

import config


@dataclass
class WasteDetection:
    cls_name: str
    category: str
    confidence: float
    x1: int
    y1: int
    x2: int
    y2: int
    recyclable: bool

    @property
    def width(self) -> int:
        return self.x2 - self.x1

    @property
    def height(self) -> int:
        return self.y2 - self.y1

    @property
    def cx(self) -> float:
        return (self.x1 + self.x2) / 2.0

    @property
    def cy(self) -> float:
        return (self.y1 + self.y2) / 2.0

    @property
    def area(self) -> int:
        return self.width * self.height


class WasteDetector:
    def __init__(self, model_path=None, conf=None, iou=None):
        self.model_path = model_path or config.MODEL_PATH
        self.conf = conf or config.CONFIDENCE_THRESHOLD
        self.iou = iou or config.IOU_THRESHOLD
        self.model = None
        self.class_names = {}
        self._category_map = {}
        self._load_model()

    def _load_model(self):
        import os
        path = self.model_path
        if not os.path.isfile(path):
            print(f"[Waste] Model '{path}' not found. Falling back to '{config.FALLBACK_MODEL}'.")
            print("[Waste] WARNING: fallback (COCO) model cannot classify waste types.")
            print("[Waste] For waste detection, provide a YOLOv8 model trained on")
            print("[Waste] plastic / paper / metal / glass / organic classes.")
            path = config.FALLBACK_MODEL
        self.model = YOLO(path)
        self.class_names = self.model.names
        self._build_category_map()
        print(f"[Waste] Loaded model with {len(self.class_names)} classes.")
        for cid, cname in self.class_names.items():
            cat = self._category_map.get(cid)
            if cat:
                print(f"  class {cid}: '{cname}' -> {cat}")

    def _build_category_map(self):
        self._category_map = {}
        for cid, cname in self.class_names.items():
            cat = self._classify(cname)
            if cat:
                self._category_map[cid] = cat

    @staticmethod
    def _classify(name: str) -> Optional[str]:
        key = name.strip().lower()
        for category, info in config.WASTE_CATEGORIES.items():
            for alias in info["aliases"]:
                if key == alias.strip().lower():
                    return category
        if "plastic" in key or "pet" in key:
            return "plastic"
        if "paper" in key or "cardboard" in key or "carton" in key:
            return "paper"
        if "metal" in key or "aluminum" in key or "steel" in key or "tin" in key or "iron" in key:
            return "metal"
        if "glass" in key:
            return "glass"
        if "organic" in key or "food" in key or "compost" in key or "biodegradable" in key:
            return "organic"
        return None

    def detect(self, frame: np.ndarray) -> List[WasteDetection]:
        results = self.model.predict(
            frame,
            conf=self.conf,
            iou=self.iou,
            imgsz=config.INFERENCE_IMG_SIZE,
            verbose=False,
        )
        detections = []
        if not results or results[0].boxes is None:
            return detections
        boxes = results[0].boxes
        for i in range(len(boxes)):
            cls_id = int(boxes.cls[i].item())
            conf_val = float(boxes.conf[i].item())
            xyxy = boxes.xyxy[i].cpu().numpy()
            cls_name = self.class_names.get(cls_id, str(cls_id))
            category = self._category_map.get(cls_id, config.DEFAULT_CATEGORY)
            cat_info = config.WASTE_CATEGORIES.get(category, config.WASTE_CATEGORIES[config.DEFAULT_CATEGORY])
            detections.append(WasteDetection(
                cls_name=cls_name,
                category=category,
                confidence=conf_val,
                x1=int(xyxy[0]),
                y1=int(xyxy[1]),
                x2=int(xyxy[2]),
                y2=int(xyxy[3]),
                recyclable=cat_info["recyclable"],
            ))
        return detections

    def get_category_info(self, category: str) -> dict:
        return config.WASTE_CATEGORIES.get(category, config.WASTE_CATEGORIES[config.DEFAULT_CATEGORY])