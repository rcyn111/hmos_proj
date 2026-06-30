"""
图片导出器 — 统一的文件写入接口。
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional


FORMAT_CONFIG = {
    "jpg": {"ext": ".jpg", "params": [cv2.IMWRITE_JPEG_QUALITY], "default_quality": 95},
    "jpeg": {"ext": ".jpg", "params": [cv2.IMWRITE_JPEG_QUALITY], "default_quality": 95},
    "png": {"ext": ".png", "params": [cv2.IMWRITE_PNG_COMPRESSION], "default_quality": 3},
    "webp": {"ext": ".webp", "params": [cv2.IMWRITE_WEBP_QUALITY], "default_quality": 90},
}


def export_image(
    image: np.ndarray,
    filepath: str,
    format: Optional[str] = None,
    quality: int = 95,
) -> str:
    """
    导出图片到文件。

    参数:
        image: numpy 图像数组 (BGR 格式)
        filepath: 输出路径
        format: 输出格式 (jpg / png / webp)。默认从后缀推断。
        quality: 质量参数 (1-100)

    返回:
        实际写入的文件路径
    """
    path = Path(filepath)
    fmt = format or path.suffix.lstrip('.').lower() or 'png'

    if fmt not in FORMAT_CONFIG:
        fmt = 'png'

    config = FORMAT_CONFIG[fmt]

    # 确保输出目录存在
    path.parent.mkdir(parents=True, exist_ok=True)

    # 确保扩展名正确
    if path.suffix.lower() != config["ext"]:
        path = path.with_suffix(config["ext"])

    # 质量映射
    if fmt == "png":
        # PNG quality: 0(无损大) ~ 9(有损小)，反转映射
        png_quality = max(0, min(9, int((100 - quality) / 11)))
        cv2.imwrite(str(path), image, [config["params"][0], png_quality])
    else:
        cv2.imwrite(str(path), image, [config["params"][0], quality])

    return str(path)
