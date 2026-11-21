"""PPE detector: runs YOLO inference and matches protective equipment to workers."""

from dataclasses import dataclass, field
from typing import List, Optional

import cv2
import numpy as np
from ultralytics import YOLO

import config


@dataclass
class Detection:
    cls_name: str
    category: str
    confidence: float
    x1: int
    y1: int
    x2: int
    y2: int

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


@dataclass
class WorkerStatus:
    person: Detection
    has_helmet: bool = False
    has_vest: bool = False
    helmet_det: Optional[Detection] = None
    vest_det: Optional[Detection] = None
    violations: List[str] = field(default_factory=list)

    @property
    def is_compliant(self) -> bool:
        return not self.violations


class PPEDetector:
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
            print(f"[PPE] Model '{path}' not found. Falling back to '{config.FALLBACK_MODEL}'.")
            print("[PPE] WARNING: fallback (COCO) model only detects 'person'.")
            print("[PPE] For full PPE detection, provide a YOLOv8 model trained on")
            print("[PPE] hardhat / vest / person classes (see README / config.py).")
            path = config.FALLBACK_MODEL
        self.model = YOLO(path)
        self.class_names = self.model.names
        self._build_category_map()
        print(f"[PPE] Loaded model with {len(self.class_names)} classes.")
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
        for category, aliases in config.PPE_CLASS_NAMES.items():
            for alias in aliases:
                if key == alias.strip().lower():
                    return category
        if "hardhat" in key or "hard-hat" in key or "helmet" in key:
            if "no" in key:
                return "no_helmet"
            return "helmet"
        if "vest" in key:
            if "no" in key:
                return "no_vest"
            return "vest"
        if key == "person" or key == "worker" or key == "people":
            return "person"
        return None

    def detect(self, frame: np.ndarray) -> List[Detection]:
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
            category = self._category_map.get(cls_id)
            if category is None:
                continue
            detections.append(Detection(
                cls_name=cls_name,
                category=category,
                confidence=conf_val,
                x1=int(xyxy[0]),
                y1=int(xyxy[1]),
                x2=int(xyxy[2]),
                y2=int(xyxy[3]),
            ))
        return detections

    @staticmethod
    def _iou(a, b) -> float:
        ax1, ay1, ax2, ay2 = a
        bx1, by1, bx2, by2 = b
        ix1 = max(ax1, bx1)
        iy1 = max(ay1, by1)
        ix2 = min(ax2, bx2)
        iy2 = min(ay2, by2)
        iw = max(0, ix2 - ix1)
        ih = max(0, iy2 - iy1)
        inter = iw * ih
        if inter == 0:
            return 0.0
        area_a = (ax2 - ax1) * (ay2 - ay1)
        area_b = (bx2 - bx1) * (by2 - by1)
        return inter / (area_a + area_b - inter)

    @staticmethod
    def _center_inside(cx, cy, box, margin=0.0) -> bool:
        x1, y1, x2, y2 = box
        return (x1 - margin) <= cx <= (x2 + margin) and (y1 - margin) <= cy <= (y2 + margin)

    def _match_ppe(self, person: Detection, ppe_items: List[Detection], region: str) -> Optional[Detection]:
        px1, py1, px2, py2 = person.x1, person.y1, person.x2, person.y2
        ph = person.height
        if region == "head":
            ry1 = py1
            ry2 = py1 + int(ph * config.HEAD_REGION_RATIO)
            region_box = (px1, ry1, px2, ry2)
        else:
            ry1 = py1 + int(ph * config.HEAD_REGION_RATIO)
            ry2 = py1 + int(ph * (config.HEAD_REGION_RATIO + config.TORSO_REGION_RATIO))
            region_box = (px1, ry1, px2, ry2)

        best = None
        best_score = 0.0
        for item in ppe_items:
            iou = self._iou(region_box, (item.x1, item.y1, item.x2, item.y2))
            center_in = self._center_inside(item.cx, item.cy, region_box)
            score = iou
            if center_in:
                score = max(score, config.CENTER_MATCH_THRESHOLD)
            if score > best_score and score >= config.IOU_MATCH_THRESHOLD:
                best_score = score
                best = item
        return best

    def analyze(self, frame: np.ndarray) -> List[WorkerStatus]:
        detections = self.detect(frame)
        persons = [d for d in detections if d.category == "person"]
        helmets = [d for d in detections if d.category == "helmet"]
        vests = [d for d in detections if d.category == "vest"]
        no_helmets = [d for d in detections if d.category == "no_helmet"]
        no_vests = [d for d in detections if d.category == "no_vest"]

        workers = []
        for person in persons:
            status = WorkerStatus(person=person)

            helmet = self._match_ppe(person, helmets, "head")
            if helmet:
                status.has_helmet = True
                status.helmet_det = helmet
            elif no_helmets:
                nh = self._match_ppe(person, no_helmets, "head")
                if nh:
                    status.has_helmet = False
                    status.helmet_det = nh

            vest = self._match_ppe(person, vests, "torso")
            if vest:
                status.has_vest = True
                status.vest_det = vest
            elif no_vests:
                nv = self._match_ppe(person, no_vests, "torso")
                if nv:
                    status.has_vest = False
                    status.vest_det = nv

            if not status.has_helmet:
                status.violations.append("NO HELMET")
            if not status.has_vest:
                status.violations.append("NO SAFETY VEST")

            workers.append(status)
        return workers