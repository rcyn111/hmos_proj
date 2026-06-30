#!/usr/bin/env python3
"""
HarmonyOS Dev Claw — 执行复盘摘要脚本（预留）

用途：对 runs/ 目录下的所有执行记录进行汇总分析。

当前状态：预留模板，v0.1.0 中功能由 Claude Code + harmony-skill-evolver 完成。

未来计划：
  - 统计各 skill 的执行次数和平均评分
  - 分析高频错误模式
  - 生成改进建议

使用：
  python3 scripts/summarize_run.py
  python3 scripts/summarize_run.py --skill harmony-requirement-analyzer
  python3 scripts/summarize_run.py --last 5
"""

import sys
import os
from datetime import datetime

PROJECT_ROOT = "$PROJECT_ROOT"
RUNS_DIR = os.path.join(PROJECT_ROOT, "runs")


def list_run_files() -> list[str]:
    """列出 runs/ 目录中所有复盘记录"""
    if not os.path.isdir(RUNS_DIR):
        return []
    files = [
        f for f in os.listdir(RUNS_DIR)
        if f.endswith(".md") and f != "README.md"
    ]
    files.sort(reverse=True)
    return files


def main():
    print("=" * 60)
    print(" HarmonyOS Dev Claw — 执行复盘摘要")
    print(f" 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    files = list_run_files()

    if not files:
        print("📝 暂无执行记录。")
        print("   当 Claw 执行 skill 后，复盘记录会自动生成在 runs/ 目录中。")
        return

    print(f"📁 共 {len(files)} 条执行记录")
    print()

    # 预留：解析 Markdown 并汇总分析
    # TODO v0.3.0: 实现解析和汇总逻辑
    print("执行记录列表：")
    for i, f in enumerate(files[:10], 1):
        print(f"  {i}. {f}")

    if len(files) > 10:
        print(f"  ... 还有 {len(files) - 10} 条")
    print()
    print("💡 提示：目前 v0.1.0 中，详细复盘分析由 harmony-skill-evolver 完成。")


if __name__ == "__main__":
    main()
