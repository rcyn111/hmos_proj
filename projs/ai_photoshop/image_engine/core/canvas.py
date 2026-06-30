"""
画布 — 管理图像状态的核心组件。

职责：
- 持有当前图像数据 (numpy array)
- 提供图像信息查询 (尺寸、色彩模式等)
- 封装底层操作调用
"""

import cv2
import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class ImageInfo:
    """图像元信息。"""
    width: int
    height: int
    channels: int
    format: str          # 文件格式: png / jpg / webp
    color_mode: str      # 色彩模式: RGB / RGBA / grayscale


class Canvas:
    """
    画布 — 包装 numpy 图像数组，提供统一的操作接口。

    用法:
        canvas = Canvas()
        canvas.load("photo.jpg")
        canvas.adjust_brightness(value=15)
        canvas.rotate(angle=90)
        canvas.save("output.jpg")
    """

    def __init__(self):
        self._image: Optional[np.ndarray] = None
        self._original: Optional[np.ndarray] = None  # 原始图像（用于 reset）
        self._info: Optional[ImageInfo] = None
        self._filepath: Optional[str] = None

    # ---- 属性 ----

    @property
    def image(self) -> np.ndarray:
        """当前图像数据 (BGR 格式)。"""
        if self._image is None:
            raise RuntimeError("画布为空，请先加载图片")
        return self._image

    @property
    def info(self) -> ImageInfo:
        if self._info is None:
            raise RuntimeError("画布为空，请先加载图片")
        return self._info

    @property
    def width(self) -> int:
        return self.info.width

    @property
    def height(self) -> int:
        return self.info.height

    @property
    def loaded(self) -> bool:
        return self._image is not None

    # ---- 文件操作 ----

    def load(self, filepath: str) -> "Canvas":
        """加载图片文件。"""
        self._filepath = filepath
        # OpenCV 读取为 BGR
        img = cv2.imread(filepath, cv2.IMREAD_UNCHANGED)
        if img is None:
            raise FileNotFoundError(f"无法加载图片: {filepath}")

        h, w = img.shape[:2]
        channels = 1 if len(img.shape) == 2 else img.shape[2]

        # 统一转为 3 通道 BGR（便于处理）
        if channels == 4:
            self._original = img.copy()
        elif channels == 1:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            self._original = img.copy()
        else:
            self._original = img.copy()

        self._image = img.copy()

        ext = filepath.rsplit('.', 1)[-1].lower() if '.' in filepath else 'png'
        color_mode = "RGBA" if channels == 4 else ("grayscale" if channels == 1 else "RGB")

        self._info = ImageInfo(
            width=w, height=h, channels=channels,
            format=ext, color_mode=color_mode,
        )
        return self

    def save(self, filepath: str, quality: int = 95) -> str:
        """保存图片到文件。"""
        cv2.imwrite(filepath, self.image, [cv2.IMWRITE_JPEG_QUALITY, quality])
        return filepath

    def reset(self) -> "Canvas":
        """恢复到原始状态。"""
        if self._original is not None:
            self._image = self._original.copy()
        return self

    # ---- 图像信息描述（供 AI 层使用） ----

    def describe(self) -> str:
        """生成图像信息描述文本。"""
        if not self.loaded:
            return "画布为空"
        i = self.info
        return f"尺寸: {i.width}x{i.height}, 格式: {i.format}, 色彩: {i.color_mode}"

    def thumbnail(self, max_size: int = 512) -> np.ndarray:
        """生成缩略图（供 UI 层预览）。"""
        h, w = self.image.shape[:2]
        scale = min(max_size / w, max_size / h, 1.0)
        if scale < 1.0:
            new_w, new_h = int(w * scale), int(h * scale)
            return cv2.resize(self.image, (new_w, new_h))
        return self.image.copy()
