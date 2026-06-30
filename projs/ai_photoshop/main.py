#!/usr/bin/env python3
"""
AI Photoshop — CLI 入口。

用法:
  # 单条指令
  python3 main.py --image cat.jpg --command "调亮一点并裁成正方形"

  # 多条指令（用 ；分隔）
  python3 main.py --image cat.jpg --command "调亮；加复古滤镜；裁成正方形"

  # 交互模式
  python3 main.py --image cat.jpg --interactive
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# 确保项目根目录在 path 中
PROJ_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJ_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJ_ROOT / "config" / ".env")

from image_engine.core.canvas import Canvas
from image_engine.core.history import HistoryManager
from ai_commander.commander import AICommander

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger('ai_photoshop')


def run_single_command(canvas: Canvas, commander: AICommander,
                       history: HistoryManager, command: str) -> bool:
    """执行单条指令。"""
    print(f"\n🤖 指令: {command}")

    try:
        result = commander.execute(canvas.image, command, history)
        canvas._image = result  # 更新画布
        print(f"✅ 完成 ({history.undo_count} 步历史记录)")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def run_interactive(canvas: Canvas, commander: AICommander,
                    history: HistoryManager):
    """交互模式。"""
    print("\n" + "=" * 60)
    print("🖼️  AI Photoshop — 交互模式")
    print("=" * 60)
    print(f"当前图片: {canvas.describe()}")
    print()
    print("命令示例:")
    print("  调亮一点")
    print("  裁成正方形")
    print("  加复古滤镜")
    print("  先模糊再转黑白")
    print("  旋转90度")
    print()
    print("输入 'undo' 撤销 | 'redo' 重做 | 'reset' 恢复原图")
    print("输入 'save' 保存 | 'history' 查看历史 | 'quit' 退出")
    print("-" * 60)

    while True:
        try:
            cmd = input("\n📝 指令: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 再见！")
            break

        if not cmd:
            continue

        # 特殊命令
        if cmd.lower() in ('quit', 'exit', 'q'):
            # 退出前保存
            save = input("保存修改? (y/n): ").strip().lower()
            if save == 'y':
                outpath = canvas._filepath or "output.jpg"
                outpath = input(f"保存路径 [{outpath}]: ").strip() or outpath
                canvas.save(outpath)
                print(f"💾 已保存到 {outpath}")
            print("👋 再见！")
            break

        elif cmd.lower() == 'undo':
            snapshot = history.undo()
            if snapshot is not None:
                canvas._image = snapshot
                print("↩️ 已撤销")
            continue

        elif cmd.lower() == 'redo':
            snapshot = history.redo()
            if snapshot is not None:
                canvas._image = snapshot
                print("↪️ 已重做")
            continue

        elif cmd.lower() == 'reset':
            canvas.reset()
            history.clear()
            print("🔄 已恢复原图")
            continue

        elif cmd.lower() == 'save':
            outpath = canvas._filepath or "output.jpg"
            outpath = input(f"保存路径 [{outpath}]: ").strip() or outpath
            canvas.save(outpath)
            print(f"💾 已保存到 {outpath}")
            continue

        elif cmd.lower() == 'history':
            items = history.get_history()
            if items:
                for i, item in enumerate(items, 1):
                    print(f"  {i}. {item}")
            else:
                print("  (无历史记录)")
            continue

        # 执行 AI 指令
        run_single_command(canvas, commander, history, cmd)


def main():
    parser = argparse.ArgumentParser(
        description='AI Photoshop — 用自然语言编辑图片',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 main.py --image cat.jpg --command "调亮一点并裁成正方形"
  python3 main.py --image cat.jpg --command "加复古滤镜；转黑白"
  python3 main.py --image cat.jpg --interactive
        """,
    )
    parser.add_argument('--image', '-i', type=str, required=True,
                        help='输入图片路径')
    parser.add_argument('--command', '-c', type=str,
                        help='编辑指令（多条用中文分号 ；分隔）')
    parser.add_argument('--output', '-o', type=str, default='output.jpg',
                        help='输出图片路径 (默认 output.jpg)')
    parser.add_argument('--interactive', action='store_true',
                        help='交互模式（可以连续输入多条指令）')

    args = parser.parse_args()

    # ---- 加载图片 ----
    if not os.path.exists(args.image):
        print(f"❌ 图片不存在: {args.image}")
        sys.exit(1)

    canvas = Canvas().load(args.image)
    history = HistoryManager(max_steps=50)
    commander = AICommander()

    print(f"📷 已加载: {args.image}")
    print(f"   {canvas.describe()}")
    print(f"   可用操作: {len(commander.registry.list_operations())} 个")
    print(f"   {', '.join(commander.registry.list_operations())}")

    # ---- 执行 ----
    if args.interactive:
        run_interactive(canvas, commander, history)
    elif args.command:
        # 支持多条指令（用中文分号分隔）
        commands = [c.strip() for c in args.command.replace('；', ';').split(';') if c.strip()]

        all_ok = True
        for i, cmd in enumerate(commands, 1):
            print(f"\n--- 第 {i}/{len(commands)} 步 ---")
            if not run_single_command(canvas, commander, history, cmd):
                all_ok = False
                print("⚠️ 后续指令继续执行...")

        # 保存
        outpath = args.output or f"{Path(args.image).stem}_edited.jpg"
        canvas.save(outpath)
        print(f"\n💾 最终结果已保存: {outpath}")
        if not all_ok:
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
