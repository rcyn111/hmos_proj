#!/usr/bin/env python3
"""
Excel 输出模块 — 将生成结果写入规范格式的 Excel 文件。

输出规则（严格）：
  - 文件名：article_outputs/generated_articles.xlsx
  - 只有四列：主题、文章正文、标题、转发文案
  - 转发文案字段包含：转发文案（2-3句）+ 替补标题（3个）
  - 不允许出现额外列
"""

import logging
import os
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------

@dataclass
class ArticleOutput:
    """单篇文章的最终输出数据。"""
    topic: str              # 主题
    body: str               # 文章正文（含图片占位符）
    title: str              # 主标题
    share_text: str         # 2-3 句转发文案
    alternative_titles: List[str]  # 3 个替补标题


def build_title_column(main_title: str, alternative_titles: List[str]) -> str:
    """
    构建"标题"列的内容。

    格式：
        主标题：xxx

        替补标题：
        1. xxx
        2. xxx
        3. xxx
    """
    parts = ["主标题：" + main_title, "", "替补标题："]
    for i, title in enumerate(alternative_titles, 1):
        import re
        cleaned = re.sub(r'^\d+[\.\、\)\s]+\s*', '', title).strip()
        parts.append(f"{i}. {cleaned}")
    return "\n".join(parts)


def build_share_column(share_text: str) -> str:
    """
    构建"转发文案"列的内容（仅转发文案，不含替补标题）。

    格式：
        1. xxx
        2. xxx
    """
    import re
    parts = []
    share_lines = [l.strip() for l in share_text.strip().split('\n') if l.strip()]
    for i, line in enumerate(share_lines, 1):
        cleaned = re.sub(r'^\d+[\.\、\)\s]+\s*', '', line).strip()
        parts.append(f"{i}. {cleaned}")
    return "\n".join(parts)


def write_to_excel(
    outputs: List[ArticleOutput],
    output_path: str = "article_outputs/generated_articles.xlsx",
) -> str:
    """
    将文章列表写入 Excel 文件。

    参数:
        outputs: 文章输出列表
        output_path: 输出文件路径

    返回:
        实际写入的文件路径

    严格保证四列：主题、文章正文、标题、转发文案
    """
    import pandas as pd

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 构建数据行
    rows = []
    for out in outputs:
        title_col = build_title_column(out.title, out.alternative_titles)
        share_col = build_share_column(out.share_text)
        rows.append({
            '主题': out.topic,
            '文章正文': out.body,
            '标题': title_col,
            '转发文案': share_col,
        })

    # 创建 DataFrame，严格指定列顺序
    df = pd.DataFrame(rows, columns=['主题', '文章正文', '标题', '转发文案'])

    # 写入 Excel
    # 使用 openpyxl 引擎以获得更好的格式控制
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='文章列表')

        # 调整列宽
        ws = writer.sheets['文章列表']
        ws.column_dimensions['A'].width = 20   # 主题
        ws.column_dimensions['B'].width = 80   # 文章正文
        ws.column_dimensions['C'].width = 30   # 标题
        ws.column_dimensions['D'].width = 40   # 转发文案

        # 设置正文列自动换行
        from openpyxl.styles import Alignment
        for row in ws.iter_rows(min_row=2, max_row=len(rows)+1):
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical='top')

    logger.info(f"Excel 文件已写入: {output_path} ({len(rows)} 行)")
    return os.path.abspath(output_path)


def validate_excel(output_path: str) -> bool:
    """
    验证生成的 Excel 文件是否符合规范。

    检查：
    - 文件存在
    - 恰好四列
    - 列名正确
    """
    import pandas as pd

    if not os.path.exists(output_path):
        logger.error(f"Excel 文件不存在: {output_path}")
        return False

    df = pd.read_excel(output_path, engine='openpyxl')
    expected_columns = ['主题', '文章正文', '标题', '转发文案']

    actual_columns = list(df.columns)
    if actual_columns != expected_columns:
        logger.error(
            f"Excel 列名不符: 期望 {expected_columns}，实际 {actual_columns}"
        )
        return False

    if len(df) == 0:
        logger.warning("Excel 文件为空（无数据行）")

    logger.info(f"Excel 验证通过: {len(df)} 行, 4 列")
    return True
