import time
import cv2
import mediapipe as mp
from modul.pengaturan import MODEL_PATH, SIDE_LOCK_FRAMES
from modul.geometri import SideLock

LM = {"shoulder": (11, 12), "elbow": (13, 14), "wrist": (15, 16), "hip": (23, 24),
      "knee": (25, 26), "ankle": (27, 28), "foot": (31, 32)}

CONNECTIONS = [(11, 12), (11, 13), (13, 15), (12, 14), (14, 16), (11, 23), (12, 24),
               (23, 24), (23, 25), (25, 27), (24, 26), (26, 28), (27, 29), (29, 31),
               (27, 31), (28, 30), (30, 32), (28, 32)]


def _vis(lm):
    v = getattr(lm, "visibility", None)
    if v is None:
        v = getattr(lm, "presence", None)
    return v or 0.0


class PoseDetector:
    def __init__(self, model_path=MODEL_PATH):
        options = mp.tasks.vision.PoseLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=model_path),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            min_pose_detection_confidence=0.5,
            min_tracking_confidence=0.5)
        self.landmarker = mp.tasks.vision.PoseLandmarker.create_from_options(options)
        self.last_ts = -1
        self.side_lock = SideLock(SIDE_LOCK_FRAMES)

    def process(self, frame, timestamp_ms=None):
        """timestamp_ms: waktu frame dalam milidetik. Untuk file video sebaiknya dari
        posisi video (bukan jam dinding). Kalau None, dipakai jam dinding."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        ts = int(time.time() * 1000) if timestamp_ms is None else int(timestamp_ms)
        ts = max(self.last_ts + 1, ts)  # MediaPipe mewajibkan timestamp selalu naik
        self.last_ts = ts
        result = self.landmarker.detect_for_video(image, ts)
        return result.pose_landmarks[0] if result.pose_landmarks else None

    def draw(self, frame, landmarks):
        h, w = frame.shape[:2]
        pts = [(int(l.x * w), int(l.y * h)) for l in landmarks]
        for a, b in CONNECTIONS:
            cv2.line(frame, pts[a], pts[b], (255, 255, 255), 2)
        for i in range(11, 33):
            cv2.circle(frame, pts[i], 4, (0, 0, 255), -1)

    def unlock_side(self):
        """Dipanggil kalau orang sempat hilang lama, agar sisi dipilih ulang."""
        self.side_lock.unlock()

    def side_points(self, landmarks, shape):
        """Ambil sisi tubuh (kiri/kanan) yang terkunci, dalam koordinat piksel."""
        h, w = shape[:2]
        vis = [sum(_vis(landmarks[idx[s]]) for idx in LM.values()) for s in (0, 1)]
        side = self.side_lock.update(vis[0], vis[1])
        return {name: (landmarks[idx[side]].x * w, landmarks[idx[side]].y * h, _vis(landmarks[idx[side]]))
                for name, idx in LM.items()}