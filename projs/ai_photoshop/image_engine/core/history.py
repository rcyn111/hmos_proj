"""
历史记录管理器 — 基于快照的 undo / redo 实现。

每步操作前自动保存快照，支持无限级撤销和重做。
个人使用场景图片不大，快照模式简单可靠。
"""

import numpy as np
from typing import List, Optional, Callable
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class HistoryEntry:
    """一条历史记录。"""
    operation_name: str      # 操作名称（如 "adjust_brightness"）
    description: str         # 人类可读的描述
    snapshot: np.ndarray     # 操作前的图像快照


class HistoryManager:
    """
    历史记录管理器。

    用法:
        history = HistoryManager(max_steps=50)
        history.save_snapshot("adjust_brightness", image, "亮度 +15")
        # ... 执行操作 ...
        if need_undo:
            image = history.undo()
    """

    def __init__(self, max_steps: int = 50):
        self._undo_stack: List[HistoryEntry] = []
        self._redo_stack: List[HistoryEntry] = []
        self._max_steps = max_steps
        self._on_change: Optional[Callable] = None

    @property
    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    @property
    def undo_count(self) -> int:
        return len(self._undo_stack)

    def save_snapshot(self, operation_name: str, image: np.ndarray, description: str = "") -> None:
        """保存操作前的快照。"""
        entry = HistoryEntry(
            operation_name=operation_name,
            description=description or operation_name,
            snapshot=image.copy(),
        )
        self._undo_stack.append(entry)
        self._redo_stack.clear()  # 新操作后清空 redo 栈

        # 限制最大步数
        if len(self._undo_stack) > self._max_steps:
            self._undo_stack.pop(0)

        logger.debug(f"快照已保存: {entry.description} (undo栈: {len(self._undo_stack)})")

        if self._on_change:
            self._on_change()

    def undo(self) -> Optional[np.ndarray]:
        """撤销上一步，返回之前的快照。"""
        if not self._undo_stack:
            logger.info("没有可撤销的操作")
            return None

        entry = self._undo_stack.pop()
        self._redo_stack.append(entry)
        logger.info(f"撤销: {entry.description}")
        return entry.snapshot

    def redo(self) -> Optional[np.ndarray]:
        """重做已撤销的步骤。"""
        if not self._redo_stack:
            logger.info("没有可重做的操作")
            return None

        entry = self._redo_stack.pop()
        self._undo_stack.append(entry)
        logger.info(f"重做: {entry.description}")
        return entry.snapshot

    def get_history(self) -> List[str]:
        """获取操作历史列表（供 UI / AI 展示）。"""
        return [entry.description for entry in self._undo_stack]

    def clear(self) -> None:
        """清空所有历史。"""
        self._undo_stack.clear()
        self._redo_stack.clear()

    def set_on_change(self, callback: Callable) -> None:
        """设置历史变化回调（供 UI 更新使用）。"""
        self._on_change = callback
