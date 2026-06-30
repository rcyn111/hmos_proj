"""
图片加载器 — 统一的文件读取接口。
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Tuple


SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif'}


def load_image(filepath: str) -> Tuple[np.ndarray, dict]:
    """
    加载图片文件。

    返回:
        (image_array, metadata)
        metadata = {"width": int, "height": int, "channels": int, "format": str}
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"图片不存在: {filepath}")

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_FORMATS:
        raise ValueError(f"不支持的格式: {suffix}。支持: {SUPPORTED_FORMATS}")

    img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"无法读取图片，文件可能已损坏: {filepath}")

    h, w = img.shape[:2]
    channels = 1 if len(img.shape) == 2 else img.shape[2]

    metadata = {
        "width": w,
        "height": h,
        "channels": channels,
        "format": suffix.lstrip('.'),
        "filesize": path.stat().st_size,
    }

    return img, metadata


def load_as_rgb(filepath: str) -> Tuple[np.ndarray, dict]:
    """加载图片并统一转为 BGR 格式。"""
    img, meta = load_image(filepath)

    if meta["channels"] == 4:
        # BGRA → BGR
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    elif meta["channels"] == 1:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    meta["channels"] = 3
    return img, meta
