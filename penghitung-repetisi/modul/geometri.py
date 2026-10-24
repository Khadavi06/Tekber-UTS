from collections import deque
import numpy as np


def angle(a, b, c):
    ba = np.subtract(a[:2], b[:2])
    bc = np.subtract(c[:2], b[:2])
    cos = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    return float(np.degrees(np.arccos(np.clip(cos, -1.0, 1.0))))


def angle_to_vertical(top, bottom):
    dx, dy = top[0] - bottom[0], top[1] - bottom[1]
    return float(np.degrees(np.arctan2(abs(dx), abs(dy) + 1e-6)))


def dist(a, b):
    return float(np.hypot(a[0] - b[0], a[1] - b[1]))


def offset_from_line(p, a, b):
    """Jarak bertanda p ke garis a-b; positif = p di bawah garis."""
    ab = np.subtract(b[:2], a[:2])
    ap = np.subtract(p[:2], a[:2])
    d = (ab[0] * ap[1] - ab[1] * ap[0]) / (np.linalg.norm(ab) + 1e-6)
    return float(d if ab[0] >= 0 else -d)


class Smoother:
    def __init__(self, window):
        self.window = window
        self.buf = {}

    def __call__(self, key, value):
        q = self.buf.setdefault(key, deque(maxlen=self.window))
        q.append(value)
        return sum(q) / len(q)