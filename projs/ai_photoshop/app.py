#!/usr/bin/env python3
"""
AI Photoshop — 桌面应用启动器。

双击此文件或在终端运行:
    python3 app.py

这会:
1. 启动 Flask 后端 API 服务器
2. 打开原生桌面窗口（macOS / Windows / Linux）
3. 窗口内显示 Photoshop 风格的 UI
4. 关闭窗口时自动停止服务器
"""

import sys
import os
import threading
import logging
from pathlib import Path

# 确保项目根目录在 path 中
PROJ_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJ_ROOT))

logging.basicConfig(level=logging.WARNING, format='%(message)s')
logger = logging.getLogger('app')

# -------- 1. 启动 Flask 后端 --------

def start_backend(port=9876):
    """在后台线程启动 Flask API 服务器。"""
    from ui.server import app
    app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)

backend_thread = threading.Thread(target=start_backend, daemon=True)
backend_thread.start()

# 等待服务器就绪
import time
import urllib.request
for _ in range(50):
    try:
        urllib.request.urlopen(f'http://127.0.0.1:9876/api/status', timeout=0.5)
        break
    except:
        time.sleep(0.1)

logger.info("✅ 后端服务已启动")

# -------- 2. 打开桌面窗口 --------

def launch_native_window():
    """使用 pywebview 打开原生桌面窗口。"""
    try:
        import webview
        # 创建原生窗口
        window = webview.create_window(
            title='AI Photoshop',
            url='http://127.0.0.1:9876',
            width=1400,
            height=900,
            min_size=(900, 600),
            confirm_close=True,
            text_select=True,
        )
        webview.start(debug=False, http_server=False)
    except ImportError:
        # pywebview 未安装，降级为打开浏览器
        import webbrowser
        logger.warning("pywebview 未安装，使用浏览器打开")
        webbrowser.open('http://127.0.0.1:9876')
        print("\n" + "="*60)
        print("🖼️  AI Photoshop 已在浏览器中打开")
        print("   http://127.0.0.1:9876")
        print()
        print("💡 如需原生桌面窗口，请安装 pywebview:")
        print("   pip install pywebview")
        print("="*60 + "\n")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 再见！")

    logger.info("窗口已关闭")


if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════╗
║         🖼️  AI Photoshop                    ║
║    用自然语言编辑图片的桌面应用               ║
║                                              ║
║  后端: Flask API (127.0.0.1:9876)           ║
║  窗口: 原生桌面窗口                          ║
║                                              ║
║  关闭此窗口即可退出应用                      ║
╚══════════════════════════════════════════════╝
    """)
    launch_native_window()
