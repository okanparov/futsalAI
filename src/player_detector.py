"""YOLOv8 player detection and optional MediaPipe pose estimation."""
import numpy as np

PERSON_CLASS = 0


class PlayerDetector:
    def __init__(self, model_path="models/yolov8n.pt", confidence=0.4):
        from ultralytics import YOLO  # agir bagimlilik, gec import
        self.model = YOLO(model_path)
        self.confidence = confidence
        self._pose = None

    def detect(self, frame):
        """Returns np.ndarray of [x1, y1, x2, y2, conf] for persons."""
        res = self.model(frame, classes=[PERSON_CLASS], conf=self.confidence, verbose=False)[0]
        if res.boxes is None or len(res.boxes) == 0:
            return np.empty((0, 5), dtype=float)
        xyxy = res.boxes.xyxy.cpu().numpy()
        conf = res.boxes.conf.cpu().numpy()[:, None]
        return np.hstack([xyxy, conf])

    def estimate_pose(self, frame):
        """Pose landmarks of the most prominent person in `frame` (or None)."""
        import cv2
        import mediapipe as mp
        if self._pose is None:
            self._pose = mp.solutions.pose.Pose(static_image_mode=True)
        result = self._pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        return result.pose_landmarks
