"""
Flask 后端 — 为桌面 App 提供 API 服务。

所有图像处理操作通过 HTTP API 暴露，前端通过 AJAX 调用。
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import io
import base64
import json
import logging
import traceback

import cv2
import numpy as np
from flask import Flask, request, jsonify, send_from_directory

from image_engine.core.history import HistoryManager
from image_engine.operations.skills import SKILL_LIBRARY
from ai_commander.commander import AICommander

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('api_server')

app = Flask(__name__, static_folder='web', static_url_path='')

# 全局状态
commander = AICommander()
history = HistoryManager(max_steps=50)
current_image: np.ndarray = None
original_image: np.ndarray = None


def image_to_base64(img: np.ndarray) -> str:
    """numpy 图像 → base64 PNG 字符串。

    注意: cv2.imencode 内部会处理 BGR→RGB 转换，
    所以直接传入 BGR 图像即可，不要手动转 RGB。
    """
    if img is None:
        return ""
    # 确保是 3 通道 BGR（灰度图转一下）
    if len(img.shape) == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    _, buf = cv2.imencode('.png', img)
    return base64.b64encode(buf).decode()


def base64_to_image(b64: str) -> np.ndarray:
    """base64 → numpy BGR 图像。"""
    data = base64.b64decode(b64.split(',')[-1] if ',' in b64 else b64)
    arr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)
    if len(img.shape) == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    return img


# ---- 路由 ----

@app.route('/')
def index():
    return send_from_directory('web', 'index.html')


@app.route('/api/status')
def api_status():
    ops = commander.registry.list_operations()
    skills = list(SKILL_LIBRARY.keys())
    return jsonify({
        'image_loaded': current_image is not None,
        'operations_count': len(ops),
        'skills_count': len(skills),
        'operations': ops,
        'skills': skills,
        'history_count': history.undo_count,
    })


@app.route('/api/upload', methods=['POST'])
def api_upload():
    global current_image, original_image, history
    try:
        data = request.json
        b64 = data.get('image', '')
        if not b64:
            return jsonify({'error': 'no image data'}), 400

        img = base64_to_image(b64)
        current_image = img.copy()
        original_image = img.copy()
        history.clear()

        h, w = img.shape[:2]
        commander.set_image_context(width=w, height=h, image=img)

        return jsonify({
            'success': True,
            'width': w,
            'height': h,
            'stats': commander._image_stats,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/preview')
def api_preview():
    """返回当前图像的 base64。"""
    if current_image is None:
        return jsonify({'image': '', 'width': 0, 'height': 0})
    h, w = current_image.shape[:2]
    return jsonify({
        'image': 'data:image/png;base64,' + image_to_base64(current_image),
        'width': w,
        'height': h,
    })


@app.route('/api/command', methods=['POST'])
def api_command():
    """执行 AI 指令。"""
    global current_image, history

    if current_image is None:
        return jsonify({'error': '请先上传图片'}), 400

    try:
        data = request.json
        command = data.get('command', '').strip()
        if not command:
            return jsonify({'error': '请输入指令'}), 400

        # 更新上下文
        h, w = current_image.shape[:2]
        commander.set_image_context(width=w, height=h, image=current_image)

        # 解析
        result = commander.parse(command)
        if not result.success:
            return jsonify({'error': result.error}), 400

        # 执行
        steps = []
        for call in result.calls:
            description = call.description or call.name
            history.save_snapshot(call.name, current_image, description)

            if call.name in SKILL_LIBRARY:
                current_image = commander.registry.execute_skill(
                    call.name, current_image, call.params)
            else:
                current_image = commander.registry.execute(
                    call.name, current_image, call.params)

            steps.append(description)

        return jsonify({
            'success': True,
            'steps': steps,
            'step_count': len(steps),
            'preview': 'data:image/png;base64,' + image_to_base64(current_image),
            'history': history.get_history(),
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/undo', methods=['POST'])
def api_undo():
    global current_image
    snapshot = history.undo()
    if snapshot is not None:
        current_image = snapshot
        return jsonify({
            'success': True,
            'message': '已撤销',
            'preview': 'data:image/png;base64,' + image_to_base64(current_image),
        })
    return jsonify({'error': '没有可撤销的操作'}), 400


@app.route('/api/redo', methods=['POST'])
def api_redo():
    global current_image
    snapshot = history.redo()
    if snapshot is not None:
        current_image = snapshot
        return jsonify({
            'success': True,
            'message': '已重做',
            'preview': 'data:image/png;base64,' + image_to_base64(current_image),
        })
    return jsonify({'error': '没有可重做的操作'}), 400


@app.route('/api/reset', methods=['POST'])
def api_reset():
    global current_image, history
    if original_image is not None:
        current_image = original_image.copy()
        history.clear()
        return jsonify({
            'success': True,
            'preview': 'data:image/png;base64,' + image_to_base64(current_image),
        })
    return jsonify({'error': '没有可恢复的图片'}), 400


@app.route('/api/manual', methods=['POST'])
def api_manual():
    """手动调整（滑块操作）。"""
    global current_image, history
    if current_image is None:
        return jsonify({'error': '请先上传图片'}), 400

    try:
        data = request.json
        operation = data.get('operation', '')
        value = data.get('value', 0)

        valid_ops = ['adjust_brightness', 'adjust_contrast', 'adjust_saturation']
        if operation not in valid_ops:
            return jsonify({'error': f'不支持的操作: {operation}'}), 400

        params = {'value': int(value)}
        history.save_snapshot(operation, current_image, f'{operation}({value})')
        current_image = commander.registry.execute(operation, current_image, params)

        return jsonify({
            'success': True,
            'preview': 'data:image/png;base64,' + image_to_base64(current_image),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/quick_filter', methods=['POST'])
def api_quick_filter():
    """快捷滤镜。"""
    global current_image, history
    if current_image is None:
        return jsonify({'error': '请先上传图片'}), 400

    try:
        data = request.json
        filter_name = data.get('filter', '')

        params = {}
        if filter_name == 'apply_sepia':
            params['intensity'] = 70
        elif filter_name in ('apply_blur',):
            params['strength'] = 10
        elif filter_name in ('apply_sharpen',):
            params['strength'] = 50

        history.save_snapshot(filter_name, current_image, filter_name)
        current_image = commander.registry.execute(filter_name, current_image, params)

        return jsonify({
            'success': True,
            'preview': 'data:image/png;base64,' + image_to_base64(current_image),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/toolbar', methods=['POST'])
def api_toolbar():
    """工具栏操作：旋转/翻转/裁正方形/缩放。"""
    global current_image, history
    if current_image is None:
        return jsonify({'error': '请先上传图片'}), 400

    try:
        data = request.json
        action = data.get('action', '')

        if action == 'rotate_cw':
            current_image = commander.registry.execute('rotate', current_image, {'angle': -90})
            desc = '顺时针旋转90°'
        elif action == 'rotate_ccw':
            current_image = commander.registry.execute('rotate', current_image, {'angle': 90})
            desc = '逆时针旋转90°'
        elif action == 'rotate_180':
            current_image = commander.registry.execute('rotate', current_image, {'angle': 180})
            desc = '旋转180°'
        elif action == 'flip_h':
            current_image = commander.registry.execute('flip', current_image, {'direction': 'horizontal'})
            desc = '水平翻转'
        elif action == 'flip_v':
            current_image = commander.registry.execute('flip', current_image, {'direction': 'vertical'})
            desc = '垂直翻转'
        elif action == 'crop_square':
            current_image = commander.registry.execute('crop_to_square', current_image, {})
            desc = '裁剪为正方形'
        elif action == 'resize':
            w = data.get('width')
            h = data.get('height')
            scale = data.get('scale')
            params = {}
            if w: params['width'] = int(w)
            if h: params['height'] = int(h)
            if scale: params['scale'] = float(scale)
            if not params:
                return jsonify({'error': '请指定尺寸或缩放比例'}), 400
            current_image = commander.registry.execute('resize', current_image, params)
            desc = f'缩放至 {current_image.shape[1]}x{current_image.shape[0]}'
        else:
            return jsonify({'error': f'未知操作: {action}'}), 400

        history.save_snapshot(action, current_image, desc)

        return jsonify({
            'success': True,
            'description': desc,
            'preview': 'data:image/png;base64,' + image_to_base64(current_image),
            'size': f'{current_image.shape[1]}x{current_image.shape[0]}',
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/save', methods=['POST'])
def api_save():
    """保存图片。"""
    if current_image is None:
        return jsonify({'error': '没有可保存的图片'}), 400

    try:
        data = request.json
        filepath = data.get('path', 'output.jpg')
        cv2.imwrite(filepath, current_image)
        return jsonify({'success': True, 'path': filepath})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def start_server(port=9876):
    """启动 Flask 服务器。"""
    logger.info(f"API 服务器启动于 http://127.0.0.1:{port}")
    app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)


if __name__ == '__main__':
    start_server()
