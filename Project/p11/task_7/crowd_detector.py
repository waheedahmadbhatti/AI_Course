"""Crowd detector: YOLO person detection + multi-object tracking via ByteTrack."""

from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
from ultralytics import YOLO

import config


@dataclass
class TrackedPerson:
    track_id: int
    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float
    frame_idx: int
    cx: float = 0.0
    cy: float = 0.0
    history: deque = field(default_factory=lambda: deque(maxlen=config.TRACK_HISTORY_LEN))

    def __post_init__(self):
        self.cx = (self.x1 + self.x2) / 2.0
        self.cy = (self.y1 + self.y2) / 2.0

    @property
    def width(self) -> int:
        return self.x2 - self.x1

    @property
    def height(self) -> int:
        return self.y2 - self.y1

    def update(self, x1, y1, x2, y2, confidence, frame_idx):
        self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2
        self.confidence = confidence
        self.frame_idx = frame_idx
        self.cx = (x1 + x2) / 2.0
        self.cy = (y1 + y2) / 2.0
        self.history.append((self.cx, self.cy))


class CrowdDetector:
    def __init__(self, model_path=None, conf=None, iou=None):
        self.model_path = model_path or config.MODEL_PATH
        self.conf = conf or config.CONFIDENCE_THRESHOLD
        self.iou = iou or config.IOU_THRESHOLD
        self.model = None
        self.class_names = {}
        self._person_class_ids = set()
        self._load_model()

    def _load_model(self):
        import os
        path = self.model_path
        if not os.path.isfile(path):
            print(f"[Crowd] Model '{path}' not found. Falling back to '{config.FALLBACK_MODEL}'.")
            print("[Crowd] The fallback COCO model detects 'person' (class 0) — suitable for crowd counting.")
            path = config.FALLBACK_MODEL
        self.model = YOLO(path)
        self.class_names = self.model.names
        self._identify_person_classes()
        print(f"[Crowd] Loaded model with {len(self.class_names)} classes.")
        print(f"[Crowd] Person class IDs: {self._person_class_ids}")

    def _identify_person_classes(self):
        self._person_class_ids = set()
        for cid, cname in self.class_names.items():
            key = cname.strip().lower()
            for alias in config.PERSON_CLASS_NAMES:
                if key == alias.strip().lower():
                    self._person_class_ids.add(cid)
                    break
        if not self._person_class_ids and 0 in self.class_names:
            self._person_class_ids.add(0)

    def track(self, frame: np.ndarray, frame_idx: int) -> List[TrackedPerson]:
        results = self.model.track(
            frame,
            conf=self.conf,
            iou=self.iou,
            imgsz=config.INFERENCE_IMG_SIZE,
            persist=config.TRACK_PERSIST,
            tracker=f"{config.TRACKER_TYPE}.yaml",
            verbose=False,
        )
        persons = []
        if not results or results[0].boxes is None:
            return persons

        boxes = results[0].boxes
        if boxes.id is None:
            return persons

        for i in range(len(boxes)):
            cls_id = int(boxes.cls[i].item())
            if cls_id not in self._person_class_ids:
                continue
            track_id = int(boxes.id[i].item())
            conf_val = float(boxes.conf[i].item())
            xyxy = boxes.xyxy[i].cpu().numpy()
            persons.append(TrackedPerson(
                track_id=track_id,
                x1=int(xyxy[0]),
                y1=int(xyxy[1]),
                x2=int(xyxy[2]),
                y2=int(xyxy[3]),
                confidence=conf_val,
                frame_idx=frame_idx,
            ))
        return persons