"""
蒙版系统 — 支持选区、局部调整、渐变遮罩。

蒙版是 0.0~1.0 的 float32 数组，与图像同尺寸：
- 1.0 = 完全应用操作
- 0.0 = 完全不应用操作
- 中间值 = 半透明混合

用法:
    mask = Mask.from_rectangle(image_shape, x=100, y=100, w=200, h=200)
    mask.feather(radius=20)
    result = mask.apply_operation(image, adjust_brightness, value=30)
"""

import cv2
import numpy as np
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class ImageStats:
    """图像统计分析结果，供 AI 规划时参考。"""
    mean_brightness: float
    dark_ratio: float     # 暗部像素占比 (< 85)
    bright_ratio: float   # 亮部像素占比 (> 170)
    has_sunlight: bool    # 是否存在明显高光区域
    has_shadow: bool      # 是否存在明显暗部区域
    dominant_colors: list # 主要颜色


class Mask:
    """
    蒙版 — 控制操作的作用范围。

    内部存储: float32 数组，值域 [0.0, 1.0]。
    尺寸: (height, width)，单通道。
    """

    def __init__(self, data: np.ndarray):
        """用已有数组创建蒙版。"""
        if data.dtype != np.float32:
            data = data.astype(np.float32) / 255.0
        self.data = np.clip(data, 0.0, 1.0)

    # ================================================================
    # 工厂方法
    # ================================================================

    @classmethod
    def full(cls, shape: Tuple[int, int]) -> "Mask":
        """创建全白蒙版（应用到整个图像）。"""
        h, w = shape[:2]
        return cls(np.ones((h, w), dtype=np.float32))

    @classmethod
    def empty(cls, shape: Tuple[int, int]) -> "Mask":
        """创建全黑蒙版（不应用任何操作）。"""
        h, w = shape[:2]
        return cls(np.zeros((h, w), dtype=np.float32))

    @classmethod
    def from_rectangle(cls, shape: Tuple[int, int],
                       x: int, y: int, w: int, h: int) -> "Mask":
        """创建矩形蒙版。"""
        mask_array = np.zeros(shape[:2], dtype=np.float32)
        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(shape[1], x + w), min(shape[0], y + h)
        mask_array[y1:y2, x1:x2] = 1.0
        return cls(mask_array)

    @classmethod
    def from_ellipse(cls, shape: Tuple[int, int],
                     cx: int, cy: int, rx: int, ry: int) -> "Mask":
        """创建椭圆蒙版。"""
        mask_array = np.zeros(shape[:2], dtype=np.float32)
        cv2.ellipse(mask_array, (cx, cy), (rx, ry), 0, 0, 360, 1.0, -1)
        return cls(mask_array)

    @classmethod
    def from_center_rect(cls, shape: Tuple[int, int],
                          ratio: float = 0.5) -> "Mask":
        """创建居中矩形蒙版（ratio = 矩形占比，如 0.5 = 中间 50% 区域）。"""
        h, w = shape[:2]
        rw, rh = int(w * ratio), int(h * ratio)
        x, y = (w - rw) // 2, (h - rh) // 2
        return cls.from_rectangle(shape, x, y, rw, rh)

    @classmethod
    def from_brightness_range(cls, image: np.ndarray,
                               min_val: int = 0, max_val: int = 255) -> "Mask":
        """根据亮度范围创建蒙版（选中亮度在 [min_val, max_val] 之间的像素）。"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        mask_array = ((gray >= min_val) & (gray <= max_val)).astype(np.float32)
        return cls(mask_array)

    @classmethod
    def from_color_range(cls, image: np.ndarray,
                          target_bgr: Tuple[int, int, int],
                          tolerance: int = 30) -> "Mask":
        """根据颜色相似度创建蒙版（选中与目标颜色接近的像素）。"""
        target = np.array(target_bgr, dtype=np.float32)
        diff = np.abs(image.astype(np.float32) - target)
        distance = np.sqrt(np.sum(diff ** 2, axis=2))
        max_dist = tolerance * np.sqrt(3)
        mask_array = (1.0 - np.clip(distance / max_dist, 0, 1)).astype(np.float32)
        return cls(mask_array)

    @classmethod
    def from_gradient(cls, shape: Tuple[int, int],
                       direction: str = "top_to_bottom") -> "Mask":
        """
        创建渐变蒙版。

        direction:
            "top_to_bottom" — 从上到下渐暗
            "bottom_to_top" — 从下到上渐暗
            "left_to_right" — 从左到右
            "center_to_edge" — 中心到边缘（径向渐变）
        """
        h, w = shape[:2]
        if direction == "top_to_bottom":
            grad = np.tile(np.linspace(1.0, 0.0, h), (w, 1)).T
        elif direction == "bottom_to_top":
            grad = np.tile(np.linspace(0.0, 1.0, h), (w, 1)).T
        elif direction == "left_to_right":
            grad = np.tile(np.linspace(1.0, 0.0, w), (h, 1))
        elif direction == "right_to_left":
            grad = np.tile(np.linspace(0.0, 1.0, w), (h, 1))
        elif direction == "center_to_edge":
            y, x = np.ogrid[:h, :w]
            cx, cy = w // 2, h // 2
            dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            max_dist = np.sqrt(cx ** 2 + cy ** 2)
            grad = np.clip(1.0 - dist / max_dist, 0, 1)
        else:
            grad = np.ones((h, w), dtype=np.float32)

        return cls(grad.astype(np.float32))

    # ================================================================
    # 蒙版操作
    # ================================================================

    def feather(self, radius: int = 10) -> "Mask":
        """羽化蒙版边缘。"""
        ksize = radius * 2 + 1
        self.data = cv2.GaussianBlur(self.data, (ksize, ksize), radius / 2)
        return self

    def invert(self) -> "Mask":
        """反转蒙版。"""
        self.data = 1.0 - self.data
        return self

    def expand(self, pixels: int = 5) -> "Mask":
        """扩展蒙版区域。"""
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (pixels*2+1, pixels*2+1))
        self.data = cv2.dilate(self.data, kernel, iterations=1)
        return self

    def shrink(self, pixels: int = 5) -> "Mask":
        """收缩蒙版区域。"""
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (pixels*2+1, pixels*2+1))
        self.data = cv2.erode(self.data, kernel, iterations=1)
        return self

    def intersect(self, other: "Mask") -> "Mask":
        """取两个蒙版的交集。"""
        self.data = np.minimum(self.data, other.data)
        return self

    def union(self, other: "Mask") -> "Mask":
        """取两个蒙版的并集。"""
        self.data = np.maximum(self.data, other.data)
        return self

    def subtract(self, other: "Mask") -> "Mask":
        """从当前蒙版中减去另一个。"""
        self.data = np.clip(self.data - other.data, 0, 1)
        return self

    # ================================================================
    # 应用操作
    # ================================================================

    def apply(self, image: np.ndarray, modified: np.ndarray) -> np.ndarray:
        """
        将修改后的图像按蒙版混合到原图。

        参数:
            image: 原始图像
            modified: 修改后的图像（完整的，非局部）

        返回:
            原图 + 蒙版区域用 modified 替换/混合
        """
        mask_3ch = np.stack([self.data] * 3, axis=-1) if len(image.shape) == 3 else self.data
        return (image.astype(np.float32) * (1 - mask_3ch) +
                modified.astype(np.float32) * mask_3ch).astype(np.uint8)

    def to_binary(self, threshold: float = 0.5) -> np.ndarray:
        """转为二值蒙版（0 或 255）。"""
        return (self.data >= threshold).astype(np.uint8) * 255

    @property
    def shape(self) -> Tuple[int, int]:
        return self.data.shape

    @property
    def coverage(self) -> float:
        """蒙版覆盖率（0.0 ~ 1.0）。"""
        return float(np.mean(self.data))


def analyze_image(image: np.ndarray) -> ImageStats:
    """
    分析图像，提取统计信息供 AI 规划时参考。

    返回 ImageStats 包含亮度分布、高光/暗部检测等。
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    mean_brightness = float(np.mean(gray))

    # 暗部: < 85
    dark_mask = gray < 85
    dark_ratio = float(np.mean(dark_mask))

    # 亮部: > 170
    bright_mask = gray > 170
    bright_ratio = float(np.mean(bright_mask))

    # 高光区域检测：亮部连通域面积 > 5%
    has_sunlight = bright_ratio > 0.05

    # 暗部区域检测
    has_shadow = dark_ratio > 0.05

    # 主要颜色（简化：取 K-means 3 个中心）
    pixels = image.reshape(-1, 3).astype(np.float32)
    # 采样以提高速度
    if len(pixels) > 5000:
        idx = np.random.choice(len(pixels), 5000, replace=False)
        pixels = pixels[idx]

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, labels, centers = cv2.kmeans(pixels, 3, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    dominant_colors = []
    for c in centers:
        # BGR → 可读描述
        b, g, r = int(c[0]), int(c[1]), int(c[2])
        dominant_colors.append(f"RGB({r},{g},{b})")

    return ImageStats(
        mean_brightness=mean_brightness,
        dark_ratio=dark_ratio,
        bright_ratio=bright_ratio,
        has_sunlight=has_sunlight,
        has_shadow=has_shadow,
        dominant_colors=dominant_colors,
    )
