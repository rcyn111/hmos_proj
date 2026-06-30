"""
测试图像操作模块。
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import cv2
import pytest

from image_engine.operations.registry import OperationRegistry
from image_engine.core.canvas import Canvas
from image_engine.core.history import HistoryManager


@pytest.fixture
def sample_image():
    """创建一张 200x200 的彩色测试图片。"""
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    # 画一个蓝色矩形
    img[50:150, 50:150] = [255, 0, 0]  # BGR: 蓝色
    # 画一个红色矩形
    img[75:125, 75:125] = [0, 0, 255]  # BGR: 红色
    return img


@pytest.fixture
def registry():
    return OperationRegistry().init_all()


class TestAdjustOperations:
    """测试色彩调整操作。"""

    def test_brightness_increase(self, sample_image, registry):
        result = registry.execute("adjust_brightness", sample_image, {"value": 50})
        assert result.shape == sample_image.shape
        # 调亮后亮度应该增加
        orig_brightness = sample_image.mean()
        new_brightness = result.mean()
        assert new_brightness > orig_brightness

    def test_brightness_decrease(self, sample_image, registry):
        result = registry.execute("adjust_brightness", sample_image, {"value": -50})
        assert result.shape == sample_image.shape
        assert result.mean() < sample_image.mean()

    def test_brightness_zero_no_change(self, sample_image, registry):
        result = registry.execute("adjust_brightness", sample_image, {"value": 0})
        # 应该几乎不变
        assert np.allclose(sample_image, result, atol=1)

    def test_contrast(self, sample_image, registry):
        result = registry.execute("adjust_contrast", sample_image, {"value": 30})
        assert result.shape == sample_image.shape

    def test_saturation(self, sample_image, registry):
        result = registry.execute("adjust_saturation", sample_image, {"value": -50})
        assert result.shape == sample_image.shape


class TestTransformOperations:
    """测试几何变换操作。"""

    def test_crop(self, sample_image, registry):
        result = registry.execute("crop", sample_image,
                                   {"x": 10, "y": 10, "width": 100, "height": 100})
        assert result.shape == (100, 100, 3)

    def test_crop_to_square(self, sample_image, registry):
        result = registry.execute("crop_to_square", sample_image, {})
        h, w = result.shape[:2]
        assert h == w
        assert h == min(sample_image.shape[:2])

    def test_resize(self, sample_image, registry):
        result = registry.execute("resize", sample_image,
                                   {"width": 100, "height": 100})
        assert result.shape == (100, 100, 3)

    def test_resize_scale(self, sample_image, registry):
        result = registry.execute("resize", sample_image, {"scale": 0.5})
        assert result.shape == (100, 100, 3)

    def test_rotate_90(self, sample_image, registry):
        result = registry.execute("rotate", sample_image, {"angle": 90})
        assert result.shape == (200, 200, 3)

    def test_rotate_45(self, sample_image, registry):
        result = registry.execute("rotate", sample_image, {"angle": 45})
        assert result.shape == (200, 200, 3)


class TestFilterOperations:
    """测试滤镜操作。"""

    def test_grayscale(self, sample_image, registry):
        result = registry.execute("apply_grayscale", sample_image, {})
        assert result.shape == (200, 200, 3)
        # 三个通道应该相等
        for c in range(3):
            assert np.allclose(result[:, :, c], result[:, :, 0], atol=1)

    def test_sepia(self, sample_image, registry):
        result = registry.execute("apply_sepia", sample_image, {"intensity": 70})
        assert result.shape == (200, 200, 3)

    def test_blur(self, sample_image, registry):
        result = registry.execute("apply_blur", sample_image, {"strength": 10})
        assert result.shape == (200, 200, 3)

    def test_sharpen(self, sample_image, registry):
        result = registry.execute("apply_sharpen", sample_image, {"strength": 50})
        assert result.shape == (200, 200, 3)


class TestOperationRegistry:
    """测试操作注册表。"""

    def test_all_operations_registered(self, registry):
        ops = registry.list_operations()
        assert len(ops) >= 11
        assert "adjust_brightness" in ops
        assert "crop_to_square" in ops
        assert "apply_grayscale" in ops

    def test_tool_definitions(self, registry):
        tools = registry.get_tool_definitions()
        assert len(tools) >= 11
        for tool in tools:
            assert "type" in tool
            assert "function" in tool
            assert "name" in tool["function"]

    def test_unknown_operation(self, registry, sample_image):
        with pytest.raises(KeyError):
            registry.execute("nonexistent_op", sample_image, {})


class TestCanvas:
    """测试画布。"""

    def test_create_and_load(self):
        # 创建临时文件
        img = np.zeros((50, 50, 3), dtype=np.uint8)
        img[:] = [128, 128, 128]  # 灰色
        tmpfile = "/tmp/test_ai_ps_canvas.jpg"
        cv2.imwrite(tmpfile, img)

        canvas = Canvas().load(tmpfile)
        assert canvas.loaded
        assert canvas.width == 50
        assert canvas.height == 50
        assert "50x50" in canvas.describe()

    def test_save(self, sample_image):
        canvas = Canvas()
        canvas._image = sample_image.copy()
        canvas._info = type('obj', (object,), {
            'width': 200, 'height': 200, 'channels': 3,
            'format': 'jpg', 'color_mode': 'RGB'
        })()

        out = canvas.save("/tmp/test_ai_ps_output.jpg")
        assert out.endswith(".jpg")


class TestHistoryManager:
    """测试历史记录。"""

    def test_snapshot_and_undo(self, sample_image):
        history = HistoryManager(max_steps=10)

        # 保存快照
        original = sample_image.copy()
        history.save_snapshot("test_op", original, "原始图片")

        # 修改图片
        modified = sample_image.copy()
        modified[:] = 255
        history.save_snapshot("test_op", modified, "变白")

        assert history.undo_count == 2
        assert history.can_undo

        # 撤销
        snapshot = history.undo()
        assert snapshot is not None
        assert np.array_equal(snapshot, modified)  # 撤销"变白"，回到原始

        # 再撤销
        snapshot = history.undo()
        assert np.array_equal(snapshot, original)
        assert not history.can_undo

    def test_redo(self, sample_image):
        history = HistoryManager(max_steps=10)
        history.save_snapshot("op", sample_image.copy(), "step1")
        history.save_snapshot("op", sample_image.copy(), "step2")

        history.undo()
        assert history.can_redo
        snapshot = history.redo()
        assert snapshot is not None

    def test_max_steps(self, sample_image):
        history = HistoryManager(max_steps=3)
        for i in range(5):
            history.save_snapshot("op", sample_image.copy(), f"step{i}")
        assert history.undo_count <= 3


class TestPipeline:
    """测试管道操作（多个操作串联）。"""

    def test_brightness_then_crop(self, sample_image, registry):
        img = registry.execute("adjust_brightness", sample_image, {"value": 20})
        img = registry.execute("crop_to_square", img, {})
        h, w = img.shape[:2]
        assert h == w

    def test_grayscale_then_sharpen(self, sample_image, registry):
        img = registry.execute("apply_grayscale", sample_image, {})
        img = registry.execute("apply_sharpen", img, {"strength": 50})
        assert img.shape == (200, 200, 3)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
