"""
几何变换操作：裁剪、缩放、旋转。
"""

import cv2
import numpy as np
from image_engine.operations.registry import ImageOperation


class Crop(ImageOperation):
    """裁剪图片到指定区域。"""

    name = "crop"
    description = "裁剪图片。用户说'裁剪''裁掉一部分''只要中间''去掉边缘'时使用。"

    def execute(self, image: np.ndarray, params: dict) -> np.ndarray:
        h, w = image.shape[:2]

        x = max(0, int(params.get("x", 0)))
        y = max(0, int(params.get("y", 0)))
        crop_w = int(params.get("width", w - x))
        crop_h = int(params.get("height", h - y))

        # 确保不超出边界
        x = min(x, w - 1)
        y = min(y, h - 1)
        crop_w = min(crop_w, w - x)
        crop_h = min(crop_h, h - y)

        return image[y:y + crop_h, x:x + crop_w].copy()

    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "裁剪区域左上角 x 坐标（像素），默认 0"},
                "y": {"type": "integer", "description": "裁剪区域左上角 y 坐标（像素），默认 0"},
                "width": {"type": "integer", "description": "裁剪宽度（像素）"},
                "height": {"type": "integer", "description": "裁剪高度（像素）"},
            },
            "required": ["width", "height"]
        }


class CropToSquare(ImageOperation):
    """裁剪为正方形（取中心区域）。"""

    name = "crop_to_square"
    description = "将图片裁剪为正方形(1:1)。用户说'裁成正方形''方形''1:1'时使用。"

    def execute(self, image: np.ndarray, params: dict) -> np.ndarray:
        h, w = image.shape[:2]
        size = min(h, w)

        # 居中裁剪
        x = (w - size) // 2
        y = (h - size) // 2

        return image[y:y + size, x:x + size].copy()

    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {},
            "required": []
        }


class Resize(ImageOperation):
    """缩放图片。"""

    name = "resize"
    description = "缩放图片尺寸。用户说'放大''缩小''改成800宽''调小一点'时使用。"

    def execute(self, image: np.ndarray, params: dict) -> np.ndarray:
        h, w = image.shape[:2]

        # 支持指定宽度或高度或比例
        new_w = params.get("width")
        new_h = params.get("height")
        scale = params.get("scale")

        if scale is not None:
            new_w = int(w * scale)
            new_h = int(h * scale)
        elif new_w is not None and new_h is not None:
            new_w, new_h = int(new_w), int(new_h)
        elif new_w is not None:
            ratio = int(new_w) / w
            new_w = int(new_w)
            new_h = int(h * ratio)
        elif new_h is not None:
            ratio = int(new_h) / h
            new_h = int(new_h)
            new_w = int(w * ratio)
        else:
            return image  # 没给参数，不变

        new_w = max(1, new_w)
        new_h = max(1, new_h)

        return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "width": {"type": "integer", "description": "目标宽度（像素）"},
                "height": {"type": "integer", "description": "目标高度（像素）"},
                "scale": {"type": "number", "description": "缩放比例。0.5=缩小一半，2.0=放大两倍"},
            },
            "required": []
        }


class Rotate(ImageOperation):
    """旋转图片。"""

    name = "rotate"
    description = "旋转图片。用户说'旋转''转90度''翻过来''竖着''横着'时使用。"

    def execute(self, image: np.ndarray, params: dict) -> np.ndarray:
        angle = float(params.get("angle", 0))
        h, w = image.shape[:2]

        # 特殊角度优化
        if angle in (90, -90, 180, 270, -180, -270):
            if angle in (90, -270):
                return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
            elif angle in (-90, 270):
                return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
            else:
                return cv2.rotate(image, cv2.ROTATE_180)

        # 一般角度旋转
        center = (w // 2, h // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(image, matrix, (w, h), borderMode=cv2.BORDER_CONSTANT)

    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "angle": {
                    "type": "number",
                    "description": "旋转角度(度)。正值逆时针，负值顺时针。90=左转90度"
                }
            },
            "required": ["angle"]
        }


class Flip(ImageOperation):
    """水平或垂直翻转图片。"""

    name = "flip"
    description = "翻转图片。用户说'翻转''镜像''反过来''水平翻转''垂直翻转'时使用。"

    def execute(self, image: np.ndarray, params: dict) -> np.ndarray:
        direction = params.get("direction", "horizontal")
        if direction == "horizontal":
            return cv2.flip(image, 1)  # 左右翻转
        elif direction == "vertical":
            return cv2.flip(image, 0)  # 上下翻转
        else:
            return image

    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "direction": {
                    "type": "string",
                    "enum": ["horizontal", "vertical"],
                    "description": "翻转方向。horizontal=左右，vertical=上下"
                }
            },
            "required": ["direction"]
        }
