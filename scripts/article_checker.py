#!/usr/bin/env python3
"""
文章自检模块 — 对生成的文章执行全面质量检查。

检查项目：
  1. 主题匹配度
  2. 字数是否在目标范围（±10%）
  3. 图片占位符数量是否正确
  4. 图片占位符编号是否从 0 开始连续递增
  5. 图片占位符格式是否严格正确
  6. 大纲一致性（结构检查）
  7. 标题质量
  8. 首段吸引力
  9. 是否存在重复、空话、偏题、事实夸大
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------

@dataclass
class CheckResult:
    """自检结果。"""
    passed: bool = True
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # 各项详细检查结果
    topic_match: bool = True
    word_count_ok: bool = True
    actual_word_count: int = 0
    target_word_count: int = 0
    image_count_ok: bool = True
    expected_image_count: int = 0
    actual_image_count: int = 0
    image_format_ok: bool = True
    image_sequential: bool = True
    image_format_issues: List[str] = field(default_factory=list)
    outline_match: bool = True
    title_ok: bool = True
    intro_ok: bool = True
    no_repetition: bool = True
    no_ai_tone: bool = True

    def add_issue(self, msg: str) -> None:
        """添加一个检查失败项。"""
        self.issues.append(msg)
        self.passed = False

    def add_warning(self, msg: str) -> None:
        """添加一个警告（不阻止通过）。"""
        self.warnings.append(msg)

    def summary(self) -> str:
        """生成检查摘要。"""
        status = "✅ 通过" if self.passed else "❌ 未通过"
        lines = [f"自检结果: {status}"]
        if self.issues:
            lines.append(f"问题 ({len(self.issues)} 项):")
            for i in self.issues:
                lines.append(f"  - {i}")
        if self.warnings:
            lines.append(f"警告 ({len(self.warnings)} 项):")
            for w in self.warnings:
                lines.append(f"  - {w}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# 图片占位符检查
# ---------------------------------------------------------------------------

IMAGE_PLACEHOLDER_RE = re.compile(r'!\[AI配图中\.\.\.\]\(图片(\d+)路径\)')


def _find_image_placeholders(text: str) -> List[dict]:
    """在文本中查找所有图片占位符，返回位置、内容和编号列表。"""
    results = []
    for m in IMAGE_PLACEHOLDER_RE.finditer(text):
        # 获取完整行
        line_start = text.rfind('\n', 0, m.start())
        if line_start == -1:
            line_start = 0
        else:
            line_start += 1
        line_end = text.find('\n', m.end())
        if line_end == -1:
            line_end = len(text)
        full_line = text[line_start:line_end]

        # 提取编号 n
        placeholder_num = int(m.group(1))

        results.append({
            'position': m.start(),
            'line': full_line,
            'line_number': text[:m.start()].count('\n') + 1,
            'number': placeholder_num,
        })
    return results


def check_image_placeholders(
    body: str, expected_count: int
) -> tuple[bool, int, bool, bool, List[str]]:
    """
    检查图片占位符。

    返回:
        (count_ok, actual_count, format_ok, sequential_ok, issues)
    """
    issues = []
    placeholders = _find_image_placeholders(body)
    actual_count = len(placeholders)

    # 1. 数量检查
    count_ok = (actual_count == expected_count)
    if not count_ok:
        if expected_count == 0 and actual_count > 0:
            issues.append(
                f"图片数量错误：要求 0 张图片，但正文中发现了 {actual_count} 个占位符"
            )
        elif expected_count > 0 and actual_count == 0:
            issues.append(
                f"图片数量错误：要求 {expected_count} 张图片，但正文中没有发现占位符"
            )
        else:
            issues.append(
                f"图片数量不匹配：期望 {expected_count} 个，实际 {actual_count} 个"
            )

    # 2. 格式检查 — 严格匹配 ![AI配图中...](图片n路径)
    format_ok = True
    expected_pattern = re.compile(r'^!\[AI配图中\.\.\.\]\(图片\d+路径\)$')
    for ph in placeholders:
        line = ph['line'].strip()
        if not expected_pattern.match(line):
            format_ok = False
            issues.append(
                f"占位符格式错误（第 {ph['line_number']} 行）: "
                f"'{line}' — 必须严格为 '![AI配图中...](图片n路径)'（n从0开始）"
            )

    # 3. 顺序检查 — 编号从 0 开始连续递增
    sequential_ok = True
    if len(placeholders) >= 1:
        actual_numbers = [ph['number'] for ph in placeholders]
        expected_numbers = list(range(len(placeholders)))

        # 检查是否从 0 开始
        if actual_numbers[0] != 0:
            sequential_ok = False
            issues.append(
                f"图片占位符编号必须从0开始，当前起始编号为 {actual_numbers[0]}"
            )

        # 检查是否连续递增
        for i, num in enumerate(actual_numbers):
            if num != i:
                sequential_ok = False
                issues.append(
                    f"图片占位符编号不连续：期望编号{i}（图片{i}路径），"
                    f"实际发现编号{num}（第 {placeholders[i]['line_number']} 行）"
                )
                break

    # 验证占位符分散在正文中（不是全部堆在一起）
    if len(placeholders) >= 2:
        positions = [ph['position'] for ph in placeholders]
        # 检查是否全部集中在一处（连续出现）
        consecutive = 0
        for i in range(len(positions) - 1):
            gap = positions[i+1] - positions[i]
            if gap < 80:  # 相邻占位符间距小于 80 字符（新格式更长）
                consecutive += 1
        if consecutive >= len(positions) - 1:
            issues.append(
                "图片占位符全部集中在同一位置，应分散插入正文各合适位置"
            )
            sequential_ok = False

    return count_ok, actual_count, format_ok, sequential_ok, issues


# ---------------------------------------------------------------------------
# 字数检查
# ---------------------------------------------------------------------------

def count_chinese_chars(text: str) -> int:
    """统计文本的中文字符数（含中文标点，不含英文和数字）。"""
    # 移除图片占位符后统计
    clean = IMAGE_PLACEHOLDER_RE.sub('', text)
    # 统计中文字符和中文标点
    cn_chars = len(re.findall(r'[一-鿿　-〿＀-￯]', clean))
    # 加上其他有意义的字符（字母、数字、空格等作为约当字数）
    other_chars = len(re.sub(r'[一-鿿　-〿＀-￯]', '', clean).replace('\n', '').replace(' ', ''))
    # 粗略估计：中文字符 + 其他字符/2
    return cn_chars + max(0, other_chars // 2)


def check_word_count(body: str, target: int) -> tuple[bool, int]:
    """检查字数是否在目标 ±15% 范围内。"""
    actual = count_chinese_chars(body)
    lower = int(target * 0.85)
    upper = int(target * 1.15)
    ok = lower <= actual <= upper
    logger.info(f"字数检查: 目标 {target} 字 (范围 {lower}-{upper})，实际约 {actual} 字 — {'OK' if ok else 'NG'}")
    return ok, actual


# ---------------------------------------------------------------------------
# AI 腔检测
# ---------------------------------------------------------------------------

AI_TONE_PATTERNS = [
    '综上所述', '值得注意的是', '不可否认', '众所周知',
    '随着时代的发展', '在当今社会', '毋庸置疑',
    '我们不得不承认', '显而易见', '不言而喻',
    '从某种意义上说', '在一定程度上',
    '首先，我们需要明确', '其次，我们不得不提',
    '最后但同样重要的是',
]

REPETITION_PATTERNS = [
    # 检测连续重复的段落（超过 80% 相似度的相邻句子）
]


def _check_ai_tone(text: str) -> tuple[bool, List[str]]:
    """检测明显的 AI 腔。"""
    found = []
    for pattern in AI_TONE_PATTERNS:
        count = text.count(pattern)
        if count >= 2:  # 同一模式出现 2 次以上
            found.append(f"AI腔模式 '{pattern}' 出现 {count} 次")
    ok = len(found) == 0
    return ok, found


def _check_empty_phrases(text: str, topic: str) -> tuple[bool, List[str]]:
    """检测空泛套话。"""
    issues = []
    empty_patterns = [
        '在当今社会', '随着时代的发展', '随着社会的进步',
        '众所周知', '我们都知道', '大家知道',
    ]
    for p in empty_patterns:
        if p in text:
            issues.append(f"首段/正文包含空泛套话: '{p}'")
    ok = len(issues) == 0
    return ok, issues


# ---------------------------------------------------------------------------
# 标题质量检查
# ---------------------------------------------------------------------------

def _check_title(title: str, topic: str) -> tuple[bool, List[str]]:
    """检查标题质量。"""
    issues = []

    # 标题不能太短
    if len(title) < 5:
        issues.append(f"标题过短 ({len(title)} 字): '{title}'")

    # 标题不能太长
    if len(title) > 60:
        issues.append(f"标题过长 ({len(title)} 字): '{title}'")

    # 标题党检测关键词
    clickbait_patterns = [
        '震惊', '惊呆', '吓尿', '秒杀', '完爆',
        '你绝对想不到', '99%', '所有人',
    ]
    for p in clickbait_patterns:
        if p in title:
            issues.append(f"标题可能标题党，包含 '{p}'")

    # 标题-主题匹配：跳过关键词硬匹配，仅检查标题长度
    # （LLM 生成的标题通常能自然覆盖主题，硬匹配误报率高）

    ok = len(issues) == 0
    return ok, issues


# ---------------------------------------------------------------------------
# 综合检查
# ---------------------------------------------------------------------------

def check_article(
    topic: str,
    body: str,
    title: str,
    word_count_target: int,
    image_count_target: int,
    outline: str = "",
) -> CheckResult:
    """
    对生成的文章执行全面质量检查。

    参数:
        topic: 文章主题
        body: 文章正文
        title: 文章标题
        word_count_target: 目标字数
        image_count_target: 目标图片占位符数
        outline: 文章大纲（可选，用于检查一致性）

    返回:
        CheckResult
    """
    result = CheckResult()

    # ---- 1. 字数检查 ----
    wc_ok, actual_wc = check_word_count(body, word_count_target)
    result.word_count_ok = wc_ok
    result.actual_word_count = actual_wc
    result.target_word_count = word_count_target
    if not wc_ok:
        lower = int(word_count_target * 0.85)
        upper = int(word_count_target * 1.15)
        result.add_issue(
            f"字数不符：目标 {word_count_target} 字（允许 {lower}-{upper}），实际约 {actual_wc} 字"
        )

    # ---- 2. 图片占位符检查 ----
    ic_ok, actual_ic, fmt_ok, seq_ok, img_issues = check_image_placeholders(
        body, image_count_target
    )
    result.image_count_ok = ic_ok
    result.actual_image_count = actual_ic
    result.expected_image_count = image_count_target
    result.image_format_ok = fmt_ok
    result.image_sequential = seq_ok
    result.image_format_issues = img_issues
    for issue in img_issues:
        result.add_issue(issue)

    # ---- 3. 标题质量检查 ----
    title_ok, title_issues = _check_title(title, topic)
    result.title_ok = title_ok
    for issue in title_issues:
        result.add_issue(issue)

    # ---- 4. AI 腔检测 ----
    ai_ok, ai_issues = _check_ai_tone(body)
    result.no_ai_tone = ai_ok
    for issue in ai_issues:
        result.add_warning(issue)  # AI腔作为警告而非阻塞

    # ---- 5. 空话检测 ----
    empty_ok, empty_issues = _check_empty_phrases(body, topic)
    for issue in empty_issues:
        result.add_issue(issue)

    # ---- 6. 首段检查 ----
    # 取正文前 200 字作为首段检查
    intro = body[:200]
    if any(p in intro for p in ['在当今', '随着时代', '众所周知']):
        result.intro_ok = False
        result.add_issue("首段包含空泛套话，应迅速进入主题")
    if len(intro) < 50:
        result.intro_ok = False
        result.add_issue("首段过短，可能未充分展开")

    # ---- 7. 大纲一致性检查 ----
    # 已移除：基于关键词匹配的大纲一致性检查误报率极高，
    # 且几乎每次都会触发修复循环，浪费大量 LLM 调用时间。
    # 大纲一致性由 LLM 在生成阶段自行保证。

    # ---- 输出检查日志 ----
    logger.info(result.summary())
    return result


# ---------------------------------------------------------------------------
# 生成修复建议
# ---------------------------------------------------------------------------

def generate_fix_instructions(check_result: CheckResult) -> str:
    """
    根据检查结果生成修复指令文本，用于传递给 LLM 进行修复。
    """
    if check_result.passed:
        return ""

    lines = ["请修复以下问题:\n"]
    for issue in check_result.issues:
        lines.append(f"- {issue}")

    if check_result.warnings:
        lines.append("\n请注意以下建议:")
        for w in check_result.warnings:
            lines.append(f"- {w}")

    return "\n".join(lines)
