#!/usr/bin/env python3
"""
输入解析模块 — 将自然语言或 Excel/CSV 输入解析为结构化 TestCase 列表。

支持两种输入方式：
  方式 A：自然语言文本（多个测例用 ；或换行分隔）
  方式 B：Excel (.xlsx) 或 CSV 文件
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------

@dataclass
class TestCase:
    """单个文章生成测例。"""
    topic: str                              # 文章主题（必填）
    word_count: int = 1000                  # 目标字数（默认 1000）
    image_count: int = 0                    # 图片占位符数量（默认 0）
    style: str = "通俗、有传播力、适合公众号或知识类平台发布"  # 写作风格
    audience: str = "通用"                   # 目标受众
    platform: str = "公众号"                 # 发布平台
    extra_requirements: str = ""            # 其他写作要求
    raw_input: str = ""                     # 原始输入文本（用于调试）

    def __repr__(self) -> str:
        return (
            f"TestCase(topic={self.topic!r}, words={self.word_count}, "
            f"images={self.image_count}, style={self.style!r})"
        )


# ---------------------------------------------------------------------------
# 默认值
# ---------------------------------------------------------------------------

DEFAULT_WORD_COUNT = 1000
DEFAULT_IMAGE_COUNT = 0
DEFAULT_STYLE = "通俗、有传播力、适合公众号或知识类平台发布"


# ---------------------------------------------------------------------------
# 自然语言解析
# ---------------------------------------------------------------------------

def _extract_topic(text: str) -> str:
    """从自然语言中提取文章主题。"""
    # 模式 1：以"XXX"为主题
    m = re.search(r'以[「「]?(.+?)[」」]?为[主]?题', text)
    if m:
        return m.group(1).strip()

    # 模式 2：关于"XXX"
    m = re.search(r'关于[「「]?(.+?)[」」]?的?文章', text)
    if m:
        return m.group(1).strip()

    # 模式 3：写一篇"XXX"的?文章
    m = re.search(r'写一篇[「「]?(.+?)[」」]?的?(?:文章|推文|文案)', text)
    if m:
        return m.group(1).strip()

    # 模式 4：以 XXX 开头（最宽松）
    m = re.search(r'以[「「]?(.+?)[」」]?(?:为|，|,)', text)
    if m:
        return m.group(1).strip()

    # 兜底：取前 30 个字符作为主题
    logger.warning("无法精确提取主题，使用前30字符作为主题")
    return text[:30].strip()


def _extract_word_count(text: str) -> int:
    """从自然语言中提取目标字数。"""
    # 匹配 "1200字" "一千字" "1000 字"
    m = re.search(r'(\d+)\s*字', text)
    if m:
        return int(m.group(1))

    # 中文数字（简单处理常见情况）
    cn_num_map = {
        '五百': 500, '八百': 800, '一千': 1000, '一千二': 1200,
        '一千五': 1500, '两千': 2000, '两千五': 2500, '三千': 3000,
    }
    for cn, num in cn_num_map.items():
        if cn in text:
            return num

    return DEFAULT_WORD_COUNT


def _extract_image_count(text: str) -> int:
    """从自然语言中提取图片占位符数量。"""
    # 匹配 "3个图片占位符" "添加2个图片" "3张图片占位符" 等
    patterns = [
        r'(\d+)\s*个图片占位符',
        r'(\d+)\s*张图片占位符',
        r'添加\s*(\d+)\s*[个张]?\s*图片',
        r'(\d+)\s*[个张]图片',
        r'图片\s*[数数量]?\s*[：:]\s*(\d+)',
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return int(m.group(1))
    return DEFAULT_IMAGE_COUNT


def _extract_style(text: str) -> str:
    """从自然语言中提取写作风格要求。"""
    style_hints = []

    # 检测风格关键词
    if any(kw in text for kw in ['营销', '推广', '广告', '销售']):
        style_hints.append('偏营销风格')
    if any(kw in text for kw in ['科普', '知识', '教育', '教程']):
        style_hints.append('偏科普风格')
    if any(kw in text for kw in ['专业', '学术', '严谨']):
        style_hints.append('专业严谨')
    if any(kw in text for kw in ['轻松', '幽默', '有趣']):
        style_hints.append('轻松幽默')
    if any(kw in text for kw in ['深度', '分析', '长文']):
        style_hints.append('深度分析')

    if style_hints:
        return '、'.join(style_hints)
    return DEFAULT_STYLE


def _extract_audience(text: str) -> str:
    """从自然语言中提取目标受众。"""
    m = re.search(r'(?:受众|读者|面向)[：:]*\s*(.+?)(?:[，,；;。]|$)', text)
    if m:
        return m.group(1).strip()
    return "通用"


def _extract_platform(text: str) -> str:
    """从自然语言中提取发布平台。"""
    platform_map = {
        '公众号': '公众号', '微信': '公众号',
        '知乎': '知乎', '头条': '今日头条',
        '小红书': '小红书', '微博': '微博',
        '官网': '官网', '博客': '博客',
    }
    for kw, plat in platform_map.items():
        if kw in text:
            return plat
    return "公众号"


def parse_single_case(text: str) -> TestCase:
    """解析单个测例的自然语言文本。"""
    text = text.strip()
    if not text:
        raise ValueError("测例文本为空")

    topic = _extract_topic(text)
    word_count = _extract_word_count(text)
    image_count = _extract_image_count(text)
    style = _extract_style(text)
    audience = _extract_audience(text)
    platform = _extract_platform(text)

    # 提取额外要求（不含主题、字数、图片数的剩余部分）
    extra = text

    return TestCase(
        topic=topic,
        word_count=word_count,
        image_count=image_count,
        style=style,
        audience=audience,
        platform=platform,
        extra_requirements=extra,
        raw_input=text,
    )


def parse_natural_language(text: str) -> List[TestCase]:
    """
    解析自然语言输入，返回 TestCase 列表。

    多个测例可用以下方式分隔：
    - 中文分号 ；
    - 英文分号 ;
    - 换行符
    """
    # 统一分隔符
    text = text.replace('；', ';')
    # 按分号分割
    parts = [p.strip() for p in text.split(';') if p.strip()]

    # 如果分号分割后只有 1 个，再尝试按换行分割
    if len(parts) == 1:
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        # 只有确实有换行分隔的多个测例才用换行分割
        if len(lines) > 1 and any(
            kw in l for kw in ['以', '主题', '文章', '写一篇']
            for l in lines
        ):
            parts = lines

    cases = []
    for part in parts:
        try:
            tc = parse_single_case(part)
            cases.append(tc)
            logger.info(f"解析测例成功: {tc}")
        except ValueError as e:
            logger.warning(f"跳过无效测例: {part[:50]}... — {e}")

    return cases


# ---------------------------------------------------------------------------
# Excel / CSV 文件解析
# ---------------------------------------------------------------------------

def parse_excel_file(filepath: str) -> List[TestCase]:
    """
    从 Excel (.xlsx) 或 CSV 文件中读取测例。

    支持的列名（优先按列读取）：
    - 主题 / topic
    - 字数 / word_count
    - 图片数量 / image_count
    - 其他要求 / extra_requirements

    如果只有一列"需求"，则按自然语言解析。
    """
    import pandas as pd

    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"输入文件不存在: {filepath}")

    if path.suffix.lower() == '.csv':
        df = pd.read_csv(filepath, encoding='utf-8')
    else:
        df = pd.read_excel(filepath, engine='openpyxl')

    logger.info(f"读取文件 {filepath}，共 {len(df)} 行")

    # 标准化列名（转小写，去空格）
    col_map = {col.lower().strip(): col for col in df.columns}

    cases = []

    # 情况 1：只有一列"需求" → 按自然语言解析
    if len(df.columns) == 1 or ('需求' in col_map and len(df.columns) <= 2):
        req_col = col_map.get('需求', df.columns[0])
        for _, row in df.iterrows():
            text = str(row[req_col])
            if pd.notna(text) and text.strip():
                cases.extend(parse_natural_language(text))
        return cases

    # 情况 2：有结构化列
    topic_col = None
    word_col = None
    image_col = None
    extra_col = None

    for cn, en in [
        ('主题', 'topic'), ('字数', 'word_count'),
        ('图片数量', 'image_count'), ('图片数', 'image_count'),
        ('其他要求', 'extra_requirements'), ('要求', 'extra_requirements'),
    ]:
        if cn in col_map:
            if cn in ('主题', 'topic'):
                topic_col = col_map[cn]
            elif cn in ('字数', 'word_count'):
                word_col = col_map[cn]
            elif cn in ('图片数量', '图片数', 'image_count'):
                image_col = col_map[cn]
            elif cn in ('其他要求', '要求', 'extra_requirements'):
                extra_col = col_map[cn]

    if topic_col is None:
        # 无法识别结构化列，退化为自然语言解析
        logger.warning("无法识别结构化列，按自然语言解析全部内容")
        all_text = '; '.join(
            str(v) for _, row in df.iterrows()
            for v in row if pd.notna(v)
        )
        return parse_natural_language(all_text)

    # 逐行读取
    for idx, row in df.iterrows():
        topic = str(row.get(topic_col, '')).strip()
        if not topic or pd.isna(row.get(topic_col)):
            logger.warning(f"第 {idx+1} 行主题为空，跳过")
            continue

        word_count = DEFAULT_WORD_COUNT
        if word_col and pd.notna(row.get(word_col)):
            try:
                word_count = int(row[word_col])
            except (ValueError, TypeError):
                word_count = _extract_word_count(str(row[word_col]))

        image_count = DEFAULT_IMAGE_COUNT
        if image_col and pd.notna(row.get(image_col)):
            try:
                image_count = int(row[image_col])
            except (ValueError, TypeError):
                image_count = _extract_image_count(str(row[image_col]))

        extra = ''
        if extra_col and pd.notna(row.get(extra_col)):
            extra = str(row[extra_col])

        tc = TestCase(
            topic=topic,
            word_count=word_count,
            image_count=image_count,
            extra_requirements=extra,
            raw_input=str(row.to_dict()),
        )
        cases.append(tc)
        logger.info(f"读取结构化测例: {tc}")

    return cases


# ---------------------------------------------------------------------------
# 内置 demo 测例
# ---------------------------------------------------------------------------

DEMO_CASES = [
    TestCase(
        topic='AI办公提效',
        word_count=800,
        image_count=2,
        style='通俗、有传播力、适合公众号或知识类平台发布',
        audience='职场人士',
        platform='公众号',
        raw_input='以"AI办公提效"为主题，写一篇800字文章，添加2个图片占位符',
    ),
    TestCase(
        topic='企业知识库建设',
        word_count=1000,
        image_count=3,
        style='通俗、有传播力、适合公众号或知识类平台发布',
        audience='企业管理者和IT负责人',
        platform='公众号',
        raw_input='以"企业知识库建设"为主题，写一篇1000字文章，添加3个图片占位符',
    ),
    TestCase(
        topic='新能源汽车出海',
        word_count=1200,
        image_count=2,
        style='通俗、有传播力、适合公众号或知识类平台发布',
        audience='汽车行业从业者和关注者',
        platform='公众号',
        raw_input='以"新能源汽车出海"为主题，写一篇1200字文章，添加2个图片占位符',
    ),
]


def get_demo_cases() -> List[TestCase]:
    """返回内置的 3 个示例测例。"""
    return DEMO_CASES.copy()
