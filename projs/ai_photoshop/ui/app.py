"""
AI Photoshop — Gradio 可视化界面。

用法:
    python3 ui/app.py
    然后浏览器打开 http://localhost:7860
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gradio as gr
import cv2
import numpy as np
import logging

from image_engine.core.canvas import Canvas
from image_engine.core.history import HistoryManager
from ai_commander.commander import AICommander

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('ai_photoshop_ui')

# 全局状态（每个会话独立）
commander = AICommander()
history = HistoryManager(max_steps=50)
current_image: np.ndarray = None
original_image: np.ndarray = None
current_filepath: str = ""


def load_image(file):
    """加载图片文件。"""
    global current_image, original_image, current_filepath, history
    if file is None:
        return None, "请上传一张图片", "", []

    filepath = file.name if hasattr(file, 'name') else str(file)
    current_filepath = filepath

    img = cv2.imread(filepath, cv2.IMREAD_UNCHANGED)
    if img is None:
        return None, "❌ 无法读取图片", "", []

    # 统一转为 BGR
    if len(img.shape) == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    current_image = img.copy()
    original_image = img.copy()
    history.clear()

    h, w = img.shape[:2]
    info = f"✅ 已加载: {w}x{h} | {filepath.rsplit('/',1)[-1]}"

    # 转为 RGB 给 Gradio 显示
    display = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return display, info, build_history_text(), build_op_list()


def execute_command(command: str):
    """执行 AI 指令 — 支持基础操作和高级 Skills。"""
    global current_image, history

    if current_image is None:
        return (
            None, "❌ 请先上传图片", build_history_text(),
            "", build_status_text(None)
        )

    if not command or not command.strip():
        return (
            get_display_image(), "请输入指令", build_history_text(),
            command, build_status_text(None)
        )

    try:
        # 一站式执行（内部包含图像分析、指令解析、操作执行）
        from image_engine.operations.skills import SKILL_LIBRARY

        # 解析指令
        h, w = current_image.shape[:2]
        commander.set_image_context(width=w, height=h, image=current_image)
        result = commander.parse(command.strip())

        if not result.success:
            return (
                get_display_image(),
                f"❌ {result.error}",
                build_history_text(),
                command,
                build_status_text(None)
            )

        # 执行操作（区分基础操作和 Skill）
        for call in result.calls:
            description = call.description or f"{call.name}"
            history.save_snapshot(call.name, current_image, description)

            if call.name in SKILL_LIBRARY:
                current_image = commander.registry.execute_skill(
                    call.name, current_image, call.params)
            else:
                current_image = commander.registry.execute(
                    call.name, current_image, call.params)

        # 构建状态
        status = build_status_text(result)

        return (
            get_display_image(),
            f"✅ 完成！{len(result.calls)} 步操作",
            build_history_text(),
            command,
            status,
        )

    except Exception as e:
        logger.error(f"执行失败: {e}")
        return (
            get_display_image(),
            f"❌ 执行失败: {e}",
            build_history_text(),
            command,
            build_status_text(None)
        )


def undo():
    """撤销上一步。"""
    global current_image
    snapshot = history.undo()
    if snapshot is not None:
        current_image = snapshot
        return get_display_image(), build_history_text(), "↩️ 已撤销"
    return get_display_image(), build_history_text(), "没有可撤销的操作"


def redo():
    """重做已撤销步骤。"""
    global current_image
    snapshot = history.redo()
    if snapshot is not None:
        current_image = snapshot
        return get_display_image(), build_history_text(), "↪️ 已重做"
    return get_display_image(), build_history_text(), "没有可重做的操作"


def reset():
    """恢复到原始图片。"""
    global current_image, history
    if original_image is not None:
        current_image = original_image.copy()
        history.clear()
        return get_display_image(), build_history_text(), "🔄 已恢复原图"
    return None, "", "没有可恢复的图片"


def manual_adjust(operation: str, value: int):
    """手动调整（不经过 AI）。"""
    global current_image, history
    if current_image is None:
        return get_display_image(), "请先上传图片"

    try:
        params = {"value": value}
        history.save_snapshot(operation, current_image, f"{operation}({value})")
        current_image = commander.registry.execute(operation, current_image, params)
        return get_display_image(), f"✅ {operation}: {value}"
    except Exception as e:
        return get_display_image(), f"❌ {e}"


def apply_filter_manual(filter_name: str, strength: int):
    """手动应用滤镜。"""
    global current_image, history
    if current_image is None:
        return get_display_image(), "请先上传图片"

    try:
        params = {}
        if filter_name in ("apply_sepia",):
            params["intensity"] = strength
        elif filter_name in ("apply_blur", "apply_sharpen"):
            params["strength"] = strength

        desc = f"{filter_name}"
        history.save_snapshot(filter_name, current_image, desc)
        current_image = commander.registry.execute(filter_name, current_image, params)
        return get_display_image(), f"✅ {filter_name}"
    except Exception as e:
        return get_display_image(), f"❌ {e}"


def save_image(filepath: str):
    """保存当前图片。"""
    global current_image
    if current_image is None:
        return "没有可保存的图片"

    path = filepath.strip() or "output.jpg"
    cv2.imwrite(path, current_image)
    return f"💾 已保存到 {path}"


# ---- 辅助函数 ----

def get_display_image():
    """将当前 BGR 图片转为 RGB 供 Gradio 显示。"""
    if current_image is None:
        return None
    return cv2.cvtColor(current_image, cv2.COLOR_BGR2RGB)


def build_history_text():
    """生成历史记录文本。"""
    items = history.get_history()
    if not items:
        return "暂无操作记录"
    lines = []
    for i, item in enumerate(items, 1):
        lines.append(f"{i}. {item}")
    return "\n".join(lines)


def build_status_text(result):
    """生成状态文本。"""
    if result is None:
        return ""
    if not result.success:
        return f"❌ {result.error}"
    lines = ["### 执行步骤\n"]
    for i, desc in enumerate(result.descriptions, 1):
        lines.append(f"{i}. {desc}")
    return "\n".join(lines)


def build_op_list():
    """生成操作列表（含基础操作和 Skills）。"""
    from image_engine.operations.skills import SKILL_LIBRARY
    lines = ["### 🔧 基础操作 (18个)\n"]
    for op in commander.registry.list_operations():
        lines.append(f"- `{op}`")
    lines.append("\n### 🎯 高级 Skills (13个)\n")
    for name, skill in SKILL_LIBRARY.items():
        lines.append(f"- **{name}**: {skill.description}")
    return "\n".join(lines)


# ---- 构建 UI ----

with gr.Blocks(title="AI Photoshop", theme=gr.themes.Soft()) as app:
    gr.Markdown("""
    # 🖼️ AI Photoshop
    **用自然语言编辑图片** — 上传图片，输入指令，AI 自动修图
    """)

    with gr.Row():
        # ====== 左栏：图片区域 ======
        with gr.Column(scale=3):
            image_display = gr.Image(
                label="图片预览",
                type="numpy",
                height=500,
            )
            file_input = gr.File(
                label="上传图片",
                file_types=["image"],
            )

            with gr.Row():
                undo_btn = gr.Button("↩ 撤销", size="sm", variant="secondary")
                redo_btn = gr.Button("↪ 重做", size="sm", variant="secondary")
                reset_btn = gr.Button("🔄 恢复原图", size="sm", variant="secondary")

        # ====== 右栏：控制区域 ======
        with gr.Column(scale=2):
            status_text = gr.Markdown("上传图片开始编辑")

            # -- AI 指令输入 --
            gr.Markdown("### 🤖 AI 指令")
            command_input = gr.Textbox(
                label="",
                placeholder="例如: 调亮一点并裁成正方形",
                lines=2,
            )
            execute_btn = gr.Button("🚀 执行 AI 指令", variant="primary", size="lg")

            # 快捷指令
            gr.Markdown("**快捷指令 (含 Skills)**:")
            with gr.Row():
                gr.Examples(
                    examples=[
                        "调亮一点",
                        "裁成正方形",
                        "转黑白",
                        "让阳光更强烈",
                        "暗部太黑了提亮一点",
                        "四周暗一点突出中间",
                        "加个暗角",
                        "黄金时刻暖光",
                        "磨皮柔肤",
                    ],
                    inputs=command_input,
                )

            # -- 手动调整 --
            gr.Markdown("---")
            gr.Markdown("### 🎚️ 手动调整")
            with gr.Row():
                brightness_slider = gr.Slider(-100, 100, value=0, step=5, label="亮度")
                brightness_btn = gr.Button("应用亮度", size="sm")
            with gr.Row():
                contrast_slider = gr.Slider(-100, 100, value=0, step=5, label="对比度")
                contrast_btn = gr.Button("应用对比度", size="sm")
            with gr.Row():
                saturation_slider = gr.Slider(-100, 100, value=0, step=5, label="饱和度")
                saturation_btn = gr.Button("应用饱和度", size="sm")

            # -- 快捷滤镜 --
            gr.Markdown("**快捷滤镜**:")
            with gr.Row():
                grayscale_btn = gr.Button("黑白", size="sm")
                sepia_btn = gr.Button("复古", size="sm")
                blur_btn = gr.Button("模糊", size="sm")
                sharpen_btn = gr.Button("锐化", size="sm")

            # -- 历史记录 --
            gr.Markdown("---")
            gr.Markdown("### 📜 操作历史")
            history_display = gr.Markdown("暂无操作记录")

            # -- 保存 --
            gr.Markdown("---")
            with gr.Row():
                save_path = gr.Textbox(label="保存路径", value="output.jpg")
                save_btn = gr.Button("💾 保存", size="sm")
            save_status = gr.Markdown("")

            # -- 可用操作 --
            with gr.Accordion("📋 可用操作列表", open=False):
                op_list = gr.Markdown(build_op_list())

    # -- 操作日志 --
    info_text = gr.Markdown("")

    # ====== 事件绑定 ======

    # 加载图片
    file_input.change(
        load_image, inputs=[file_input],
        outputs=[image_display, info_text, history_display, op_list]
    )

    # AI 指令执行（回车触发）
    command_input.submit(
        execute_command, inputs=[command_input],
        outputs=[image_display, info_text, history_display, command_input, status_text]
    )
    execute_btn.click(
        execute_command, inputs=[command_input],
        outputs=[image_display, info_text, history_display, command_input, status_text]
    )

    # 撤销/重做/重置
    undo_btn.click(undo, inputs=[], outputs=[image_display, history_display, info_text])
    redo_btn.click(redo, inputs=[], outputs=[image_display, history_display, info_text])
    reset_btn.click(reset, inputs=[], outputs=[image_display, history_display, info_text])

    # 手动调整
    brightness_btn.click(
        manual_adjust, inputs=[gr.State("adjust_brightness"), brightness_slider],
        outputs=[image_display, info_text]
    )
    contrast_btn.click(
        manual_adjust, inputs=[gr.State("adjust_contrast"), contrast_slider],
        outputs=[image_display, info_text]
    )
    saturation_btn.click(
        manual_adjust, inputs=[gr.State("adjust_saturation"), saturation_slider],
        outputs=[image_display, info_text]
    )

    # 快捷滤镜
    grayscale_btn.click(
        apply_filter_manual, inputs=[gr.State("apply_grayscale"), gr.State(0)],
        outputs=[image_display, info_text]
    )
    sepia_btn.click(
        apply_filter_manual, inputs=[gr.State("apply_sepia"), gr.State(70)],
        outputs=[image_display, info_text]
    )
    blur_btn.click(
        apply_filter_manual, inputs=[gr.State("apply_blur"), gr.State(10)],
        outputs=[image_display, info_text]
    )
    sharpen_btn.click(
        apply_filter_manual, inputs=[gr.State("apply_sharpen"), gr.State(50)],
        outputs=[image_display, info_text]
    )

    # 保存
    save_btn.click(save_image, inputs=[save_path], outputs=[save_status])


if __name__ == '__main__':
    app.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        inbrowser=True,
        show_error=True,
    )
