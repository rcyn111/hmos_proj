"""
滤镜操作：黑白、复古、模糊、锐化。
"""

import cv2
import numpy as np
from image_engine.operations.registry import ImageOperation


class GrayscaleFilter(ImageOperation):
    """黑白滤镜。"""

    name = "apply_grayscale"
    description = "将图片转为黑白。用户说'黑白''去色''灰色''黑白的'时使用。"

    def execute(self, image: np.ndarray, params: dict) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # 转回 3 通道以保持与其他操作兼容
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {},
            "required": []
        }


class SepiaFilter(ImageOperation):
    """复古/怀旧滤镜。"""

    name = "apply_sepia"
    description = "给图片添加复古/怀旧/老照片效果。用户说'复古''怀旧''老照片''泛黄'时使用。"

    def execute(self, image: np.ndarray, params: dict) -> np.ndarray:
        intensity = max(0, min(100, int(params.get("intensity", 70)))) / 100.0

        # 先转灰度
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR).astype(np.float32)

        # Sepia 矩阵
        sepia = image.astype(np.float32)
        sepia = cv2.transform(sepia, np.array([
            [0.393, 0.769, 0.189],
            [0.349, 0.686, 0.168],
            [0.272, 0.534, 0.131],
        ]))
        sepia = np.clip(sepia, 0, 255)

        # 混合：intensity 控制复古强度
        result = image.astype(np.float32) * (1 - intensity) + sepia * intensity
        return np.clip(result, 0, 255).astype(np.uint8)

    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "intensity": {
                    "type": "integer",
                    "description": "复古效果强度 0-100。0=原图，100=完全复古。默认 70"
                }
            },
            "required": []
        }


class BlurFilter(ImageOperation):
    """模糊滤镜。"""

    name = "apply_blur"
    description = "模糊/虚化图片。用户说'模糊''虚化''背景虚化''柔化'时使用。"

    def execute(self, image: np.ndarray, params: dict) -> np.ndarray:
        strength = max(1, min(50, int(params.get("strength", 10))))
        # 确保 kernel size 为奇数
        ksize = strength * 2 + 1
        return cv2.GaussianBlur(image, (ksize, ksize), 0)

    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "strength": {
                    "type": "integer",
                    "description": "模糊强度 1-50。'稍微模糊'=5，'很模糊'=25。默认 10"
                }
            },
            "required": []
        }


class SharpenFilter(ImageOperation):
    """锐化滤镜。"""

    name = "apply_sharpen"
    description = "锐化图片，让边缘更清晰。用户说'锐化''清晰一点''有点糊''不够清楚'时使用。"

    def execute(self, image: np.ndarray, params: dict) -> np.ndarray:
        strength = max(1, min(100, int(params.get("strength", 50)))) / 100.0

        # 拉普拉斯锐化
        blurred = cv2.GaussianBlur(image, (3, 3), 0)
        detail = image.astype(np.float32) - blurred.astype(np.float32)
        result = image.astype(np.float32) + detail * strength * 2
        return np.clip(result, 0, 255).astype(np.uint8)

    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "strength": {
                    "type": "integer",
                    "description": "锐化强度 1-100。'稍微锐化'=30，'很锐'=80。默认 50"
                }
            },
            "required": []
        }
