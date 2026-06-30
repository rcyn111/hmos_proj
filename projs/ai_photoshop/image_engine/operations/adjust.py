"""
色彩调整操作：亮度、对比度、饱和度。
"""

import cv2
import numpy as np
from image_engine.operations.registry import ImageOperation


class AdjustBrightness(ImageOperation):
    """调整图像亮度。"""

    name = "adjust_brightness"
    description = "调整图片亮度。用户说'调亮''太暗了''亮一点'时使用此操作。"

    def execute(self, image: np.ndarray, params: dict) -> np.ndarray:
        """
        value: int, -100 到 +100
            -100 = 全黑, 0 = 不变, +100 = 全白
        """
        value = params.get("value", 0)
        # 限制范围
        value = max(-100, min(100, int(value)))

        # 使用 HSV 空间的 V 通道调整亮度
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
        # delta: -100→-255, +100→+255
        delta = value * 2.55
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] + delta, 0, 255)
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "value": {
                    "type": "integer",
                    "description": "亮度调整值，范围-100到100。负数变暗，正数变亮。'稍微调亮'约+10~15，'很亮'约+40~60"
                }
            },
            "required": ["value"]
        }


class AdjustContrast(ImageOperation):
    """调整图像对比度。"""

    name = "adjust_contrast"
    description = "调整图片对比度。用户说'对比度强一点''画面发灰''层次感不够'时使用。"

    def execute(self, image: np.ndarray, params: dict) -> np.ndarray:
        value = params.get("value", 0)
        value = max(-100, min(100, int(value)))

        # 使用公式: new = (old - 128) * factor + 128
        # factor: -100→0, 0→1.0, +100→3.0
        factor = 1.0 + value / 50.0
        result = (image.astype(np.float32) - 128) * factor + 128
        return np.clip(result, 0, 255).astype(np.uint8)

    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "value": {
                    "type": "integer",
                    "description": "对比度调整值，范围-100到100。负数降低对比度，正数增强对比度。'稍微'约+10~15"
                }
            },
            "required": ["value"]
        }


class AdjustSaturation(ImageOperation):
    """调整图像饱和度。"""

    name = "adjust_saturation"
    description = "调整图片饱和度/鲜艳度。用户说'颜色鲜艳一点''饱和度低一点''褪色''黑白'时使用。"

    def execute(self, image: np.ndarray, params: dict) -> np.ndarray:
        value = params.get("value", 0)
        value = max(-100, min(100, int(value)))

        # 使用 HSV 空间的 S 通道调整饱和度
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
        factor = 1.0 + value / 100.0  # -100→0, 0→1.0, +100→2.0
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * factor, 0, 255)
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "value": {
                    "type": "integer",
                    "description": "饱和度调整值，范围-100到100。-100完全去色(黑白)，0不变，+100极鲜艳"
                }
            },
            "required": ["value"]
        }
