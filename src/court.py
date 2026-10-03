"""Referans kare pikselinden saha metresine donusum (4 nokta kalibrasyonu)."""
import cv2
import numpy as np


def court_homography(points_px, court_size_m):
    """points_px: referans karede sahanin 4 kosesi, sirayla sol-ust, sag-ust, sag-alt, sol-alt.
    Donus: piksel -> metre 3x3 matrisi."""
    pts = np.array(points_px, dtype=np.float32).reshape(4, 2)
    w, h = court_size_m
    dst = np.array([[0, 0], [w, 0], [w, h], [0, h]], dtype=np.float32)
    return cv2.getPerspectiveTransform(pts, dst).astype(float)
