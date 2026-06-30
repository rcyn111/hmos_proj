"""
局部调整操作 — 支持蒙版的区域操作。

这些操作接受额外的 mask_type 参数来选择操作的作用范围。
AI 在规划时会先用这些操作 + 合适的 mask 来实现复杂的局部编辑。
"""

import cv2
import numpy as np
from image_engine.operations.registry import ImageOperation
from image_engine.core.mask import Mask


# ---- 局部调整（带 mask_type） ----

class LocalBrightness(ImageOperation):
    """只对图像的一部分调整亮度。"""

    name = "local_brightness"
    description = "调整指定区域的亮度。可选择'亮部''暗部''中心''四周'等区域。用户说'暗部调亮''高光压暗''四周暗一点'时使用。"

    def execute(self, image: np.ndarray, params: dict) -> np.ndarray:
        value = int(params.get("value", 0))
        region = params.get("region", "center")  # center / dark_areas / bright_areas / top / bottom

        mask = self._get_mask(image, region, params)
        modified = _adjust_brightness(image, value)
        return mask.apply(image, modified)

    def _get_mask(self, image, region, params):
        h, w = image.shape[:2]
        if region == "center":
            mask = Mask.from_ellipse(image.shape, w//2, h//2, w//3, h//3)
        elif region == "dark_areas":
            threshold = int(params.get("threshold", 85))
            mask = Mask.from_brightness_range(image, 0, threshold)
        elif region == "bright_areas":
            threshold = int(params.get("threshold", 170))
            mask = Mask.from_brightness_range(image, threshold, 255)
        elif region == "top":
            mask = Mask.from_rectangle(image.shape, 0, 0, w, h//2)
        elif region == "bottom":
            mask = Mask.from_rectangle(image.shape, 0, h//2, w, h//2)
        else:
            mask = Mask.from_center_rect(image.shape, 0.5)
        mask.feather(radius=int(params.get("feather", 15)))
        return mask

    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "value": {"type": "integer", "description": "亮度调整值 -100到100。正数调亮，负数调暗"},
                "region": {"type": "string", "enum": ["dark_areas", "bright_areas", "center", "top", "bottom"],
                           "description": "调整区域。'dark_areas'=暗部，'bright_areas'=高光，'center'=中间"},
                "feather": {"type": "integer", "description": "边缘羽化像素，默认15"},
            },
            "required": ["value", "region"]
        }


class LocalContrast(ImageOperation):
    """局部对比度调整。"""

    name = "local_contrast"
    description = "调整指定区域的对比度。用户说'暗部对比度''高光柔和一点'时使用。"

    def execute(self, image, params):
        value = int(params.get("value", 0))
        region = params.get("region", "center")
        mask = LocalBrightness()._get_mask(image, region, params)
        modified = _adjust_contrast(image, value)
        return mask.apply(image, modified)

    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "value": {"type": "integer", "description": "对比度调整值 -100到100"},
                "region": {"type": "string", "enum": ["dark_areas", "bright_areas", "center"],
                           "description": "调整区域"},
            },
            "required": ["value", "region"]
        }


class LocalSaturation(ImageOperation):
    """局部饱和度调整。"""

    name = "local_saturation"
    description = "调整指定区域的饱和度。用户说'天空更蓝''肤色更自然'时使用。"

    def execute(self, image, params):
        value = int(params.get("value", 0))
        region = params.get("region", "center")
        mask = LocalBrightness()._get_mask(image, region, params)
        modified = _adjust_saturation(image, value)
        return mask.apply(image, modified)

    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "value": {"type": "integer", "description": "饱和度调整值 -100到100"},
                "region": {"type": "string", "enum": ["bright_areas", "dark_areas", "center"],
                           "description": "调整区域"},
            },
            "required": ["value", "region"]
        }


class LocalSharpen(ImageOperation):
    """局部锐化。"""

    name = "local_sharpen"
    description = "锐化指定区域。用户说'眼睛更清晰''文字更锐'时使用。"

    def execute(self, image, params):
        strength = int(params.get("strength", 50))
        region = params.get("region", "center")
        mask = LocalBrightness()._get_mask(image, region, params)
        modified = _sharpen(image, strength)
        return mask.apply(image, modified)

    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "strength": {"type": "integer", "description": "锐化强度 1-100"},
                "region": {"type": "string", "enum": ["center", "bright_areas"],
                           "description": "调整区域"},
            },
            "required": ["strength", "region"]
        }


class LocalBlur(ImageOperation):
    """局部模糊。"""

    name = "local_blur"
    description = "模糊指定区域。用户说'背景模糊''四周虚化'时使用。"

    def execute(self, image, params):
        strength = int(params.get("strength", 10))
        region = params.get("region", "edges")  # edges = 四周
        h, w = image.shape[:2]
        if region == "edges":
            mask = Mask.from_center_rect(image.shape, 0.4).invert()
        else:
            mask = Mask.from_center_rect(image.shape, 0.5)
        mask.feather(radius=20)
        modified = _blur(image, strength)
        return mask.apply(image, modified)

    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "strength": {"type": "integer", "description": "模糊强度 1-50"},
                "region": {"type": "string", "enum": ["edges", "center"],
                           "description": "模糊区域，edges=四周背景"},
            },
            "required": ["strength", "region"]
        }


class DodgeOperation(ImageOperation):
    """减淡 — 提亮特定色调范围。"""

    name = "dodge"
    description = "减淡：提亮中调/高光区域，增强立体感。用户说'提亮一点''减淡'时使用。"

    def execute(self, image, params):
        value = int(params.get("value", 15))
        target = params.get("target", "midtones")  # midtones / highlights

        if target == "highlights":
            threshold = 170
        else:
            threshold = 100

        mask = Mask.from_brightness_range(image, threshold, 255)
        mask.feather(radius=10)

        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] + value * 2.55, 0, 255)
        modified = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

        return mask.apply(image, modified)

    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "value": {"type": "integer", "description": "减淡强度 1-40"},
                "target": {"type": "string", "enum": ["midtones", "highlights"],
                           "description": "目标色调范围"},
            },
            "required": ["value"]
        }


class BurnOperation(ImageOperation):
    """加深 — 压暗特定色调范围。"""

    name = "burn"
    description = "加深：压暗中调/阴影区域，增强立体感。用户说'暗一点''加深'时使用。"

    def execute(self, image, params):
        value = int(params.get("value", 15))
        target = params.get("target", "midtones")

        if target == "shadows":
            max_val = 130
        else:
            max_val = 200

        mask = Mask.from_brightness_range(image, 0, max_val)
        mask.feather(radius=10)

        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] - value * 2.55, 0, 255)
        modified = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

        return mask.apply(image, modified)

    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "value": {"type": "integer", "description": "加深强度 1-40"},
                "target": {"type": "string", "enum": ["midtones", "shadows"],
                           "description": "目标色调范围"},
            },
            "required": ["value"]
        }


# ---- 辅助函数 ----

def _adjust_brightness(image, value):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 2] = np.clip(hsv[:, :, 2] + value * 2.55, 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)


def _adjust_contrast(image, value):
    factor = 1.0 + value / 50.0
    result = (image.astype(np.float32) - 128) * factor + 128
    return np.clip(result, 0, 255).astype(np.uint8)


def _adjust_saturation(image, value):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
    factor = 1.0 + value / 100.0
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * factor, 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)


def _sharpen(image, strength):
    ksize = max(1, min(25, strength // 4 * 2 + 1))
    blurred = cv2.GaussianBlur(image, (ksize, ksize), 0)
    detail = image.astype(np.float32) - blurred.astype(np.float32)
    result = image.astype(np.float32) + detail * (strength / 25)
    return np.clip(result, 0, 255).astype(np.uint8)


def _blur(image, strength):
    ksize = max(1, min(51, strength * 2 + 1))
    return cv2.GaussianBlur(image, (ksize, ksize), 0)
