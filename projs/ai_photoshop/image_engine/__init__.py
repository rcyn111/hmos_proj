"""
AI Photoshop — 图像处理引擎。

提供画布管理、图层系统、操作注册、文件读写等底层能力。
所有操作遵循统一接口，便于 AI 层调用。
"""

from image_engine.core.canvas import Canvas
from image_engine.core.history import HistoryManager
from image_engine.operations.registry import OperationRegistry

__all__ = ["Canvas", "HistoryManager", "OperationRegistry"]
