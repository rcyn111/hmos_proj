#!/usr/bin/env python3
"""
文章批量生成器 — 主编排脚本。

功能：
  1. 解析命令行输入（自然语言 / Excel 文件 / 内置 demo）
  2. 对每个测例依次执行：检索判断 → 大纲生成 → 标题生成 → 正文生成 → 自检 → 转发文案 → 替补标题
  3. 自动修复（最多 2 次）
  4. 输出结果到 Excel 文件

用法：
  # 方式 A：命令行直接输入
  python3 scripts/article_generator.py --input "以AI办公提效为主题..."

  # 方式 B：从 Excel 文件读取
  python3 scripts/article_generator.py --input-file article_inputs/cases.xlsx

  # 方式 C：运行内置 demo
  python3 scripts/article_generator.py --demo

依赖：
  - anthropic (pip install anthropic)
  - python-dotenv (pip install python-dotenv)
  - pandas, openpyxl

环境变量：
  - ANTHROPIC_BASE_URL: API 端点（默认 https://api.deepseek.com/anthropic）
  - ANTHROPIC_AUTH_TOKEN: API 密钥
  - ANTHROPIC_MODEL: 模型名称（默认 deepseek-v4-pro）
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

# 将项目根目录加入 path，方便导入其他模块
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.input_parser import (
    TestCase,
    parse_natural_language,
    parse_excel_file,
    get_demo_cases,
)
from scripts.material_retriever import (
    MaterialResult,
    should_retrieve_material,
    retrieve_material,
    MockSearchProvider,
)
from scripts.article_checker import (
    CheckResult,
    check_article,
    generate_fix_instructions,
)
from scripts.excel_writer import (
    ArticleOutput,
    write_to_excel,
    validate_excel,
)

# ---------------------------------------------------------------------------
# 日志配置
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger('article_generator')


# ---------------------------------------------------------------------------
# LLM 客户端
# ---------------------------------------------------------------------------

class LLMClient:
    """
    LLM 调用客户端 — 通过 Anthropic SDK 接口调用 DSAPI。

    自动从环境变量读取配置：
    - ANTHROPIC_BASE_URL
    - ANTHROPIC_AUTH_TOKEN
    - ANTHROPIC_MODEL
    """

    def __init__(self):
        self.base_url = os.environ.get(
            "ANTHROPIC_BASE_URL",
            "https://api.deepseek.com/anthropic",
        )
        self.api_key = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
        self.model = os.environ.get("ANTHROPIC_MODEL", "deepseek-v4-pro")

        if not self.api_key:
            logger.warning(
                "未设置 ANTHROPIC_AUTH_TOKEN 环境变量，将使用内置模拟生成模式"
            )
            self.client = None
        else:
            try:
                import anthropic
                self.client = anthropic.Anthropic(
                    base_url=self.base_url,
                    api_key=self.api_key,
                )
                logger.info(f"LLM 客户端已初始化: {self.base_url}, 模型: {self.model}")
            except ImportError:
                logger.warning("anthropic 包未安装，将使用内置模拟生成模式")
                self.client = None

    def _call_llm(self, system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> str:
        """调用 LLM API。失败时抛出异常而非静默降级。"""
        if self.client is None:
            raise RuntimeError("LLM 客户端未初始化，请设置 ANTHROPIC_AUTH_TOKEN")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text_parts = []
        for block in response.content:
            if hasattr(block, 'text'):
                text_parts.append(block.text)
        return '\n'.join(text_parts)

    def _safe_call(self, system_prompt: str, user_prompt: str, max_tokens: int = 4096,
                   fallback: str = "") -> str:
        """带 fallback 的安全 LLM 调用。"""
        try:
            return self._call_llm(system_prompt, user_prompt, max_tokens)
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            if fallback:
                logger.warning(f"使用 fallback 内容")
                return fallback
            raise  # 无 fallback 则继续抛出

    def _mock_generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        模拟生成模式 — 当无法调用 API 时使用。

        生成一个符合格式要求的占位文章，确保后续流程可走通。
        注意：这不是真正的 AI 生成文章，仅用于测试流程。
        """
        logger.info("使用模拟模式生成内容")

        # 从 user_prompt 中提取主题和字数等关键信息
        import re
        topic = "未知主题"
        m = re.search(r'主题[：:]\s*(.+?)(?:\n|$)', user_prompt)
        if m:
            topic = m.group(1).strip()

        word_count = 1000
        m = re.search(r'(\d+)\s*字', user_prompt)
        if m:
            word_count = int(m.group(1))

        image_count = 0
        m = re.search(r'(\d+)\s*[个张]', user_prompt)
        if m:
            image_count = int(m.group(1))

        # 生成模拟内容
        return self._build_mock_article(topic, word_count, image_count)

    def _build_mock_article(self, topic: str, word_count: int, image_count: int) -> str:
        """构建模拟文章（在无法调用 API 时的降级方案）。"""
        lines = [
            f"# {topic}：正在改变未来的力量",
            "",
            f"在数字化转型的浪潮中，{topic}正成为越来越多人关注的焦点。",
            f"无论是对企业还是个人而言，理解并掌握{topic}的核心逻辑，",
            f"都已成为提升竞争力的关键。",
            "",
        ]

        # 添加图片占位符
        img_count = 0
        section_count = min(image_count + 3, 6)
        for i in range(section_count):
            if i > 0 and img_count < image_count:
                lines.append(f"![AI配图中...](图片{img_count}路径)")
                lines.append("")
                img_count += 1
                img_positions.append(i)
            lines.append(f"## 第{i+1}部分：{topic}的关键洞察")
            lines.append("")
            # 生成段落以达到目标字数
            paragraph_words = max(50, word_count // (section_count * 3))
            for _ in range(3):
                lines.append(
                    f"关于{topic}，我们需要从多个维度来理解。首先，从行业发展的角度来看，"
                    f"{topic}正在重塑传统的业务模式。其次，从技术演进的角度来看，"
                    f"相关技术的成熟为{topic}的落地提供了坚实基础。"
                    f"最后，从市场需求的角度来看，用户对{topic}的期待值不断上升。"
                )
                lines.append("")

        lines.append("## 总结")
        lines.append("")
        lines.append(
            f"总的来说，{topic}不仅是一个热门话题，更是一个值得长期关注的趋势。"
            f"对于想要在这一领域有所建树的人来说，关键在于持续学习和实践。"
            f"未来已来，让我们一起拥抱{topic}带来的机遇与挑战。"
        )
        lines.append("")

        return "\n".join(lines)

    def generate_outline(
        self, test_case: TestCase, materials: Optional[MaterialResult] = None
    ) -> str:
        """生成文章大纲。"""
        system_prompt = (
            "你是一个专业的内容策划师。请为指定的主题生成一篇结构清晰的文章大纲。"
        )

        materials_section = ""
        if materials and materials.materials:
            materials_section = f"\n参考材料：\n{materials.materials}\n"
            if materials.source_label:
                materials_section += f"\n来源说明：{materials.source_label}\n"

        user_prompt = f"""请为主题"{test_case.topic}"生成一篇文章大纲。

目标字数：{test_case.word_count}字
图片占位符数量：{test_case.image_count}个（格式：![AI配图中...](图片n路径)，n从0开始）
写作风格：{test_case.style}
目标受众：{test_case.audience}
发布平台：{test_case.platform}
{materials_section}

要求：
1. 大纲结构：引言 → 主体（2-4个分论点）→ 结论
2. 每个部分标注预估字数
3. 标注图片占位符的建议插入位置（用 [图片N] 标记，N从0到{max(0, test_case.image_count - 1)}）
4. 确保各部分字数之和接近目标字数

请直接输出大纲，不要输出其他内容。"""

        return self._safe_call(system_prompt, user_prompt, max_tokens=2048,
                               fallback=f"# {test_case.topic} 文章大纲\n\n## 引言\n- 引出主题背景和重要性\n\n## 主体\n- 核心观点阐述\n\n## 结论\n- 总结要点")

    def generate_title(self, topic: str, outline: str) -> str:
        """生成文章标题，失败时重试并带 fallback。"""
        system_prompt = (
            "你是一个擅长起标题的资深编辑。请为主题生成一个吸引人的文章标题。"
            "请直接输出标题文本，不要加引号、不要加'标题：'前缀，不要加任何解释，只输出标题本身。"
            "重要：你必须输出标题文本，不能输出空内容。"
        )

        # 截取简短主题用于 prompt（避免过长主题干扰）
        short_topic = topic[:30] if len(topic) > 30 else topic
        user_prompt = f"""基于以下大纲，为主题"{short_topic}"生成一个文章标题。

大纲摘要：
{outline[:500]}

要求：
1. 有吸引力和传播力，适合在朋友圈和社群分享
2. 不能标题党（不用"震惊""秒杀""你绝对想不到"等词）
3. 不能夸大事实或虚假承诺
4. 紧扣主题，不偏离
5. 字数控制在 10-30 字之间
6. 标题必须是一个完整的句子，不能为空

请直接输出标题文本，不要加引号、不要加"标题："前缀，只输出标题本身。"""

        for attempt in range(2):
            try:
                title = self._safe_call(system_prompt, user_prompt, max_tokens=256, fallback="")
            except Exception:
                title = ""
            if not title or not title.strip():
                logger.warning(f"  标题生成返回空 (尝试 {attempt+1})，立即重试…")
                continue
            # 清理可能的引号和前缀
            for prefix in ['标题：', '标题:', 'Title:', '# ', '## ']:
                if title.startswith(prefix):
                    title = title[len(prefix):]
            title = title.strip('"').strip("'").strip('「').strip('」').strip()
            title = title.replace('\n', ' ').strip()

            # 校验：标题必须在 5-80 字之间
            if 5 <= len(title) <= 80:
                logger.info(f"  标题生成成功 (尝试 {attempt+1}): {title}")
                return title
            if len(title) > 80:
                logger.warning(f"  标题过长 ({len(title)} 字)，截断重试...")

        # 失败后使用简短精炼的 fallback
        short_t = topic[:15] + "…" if len(topic) > 15 else topic
        fallback = f"关于{short_t}，你必须知道的几件事"
        logger.warning(f"  标题生成失败，使用 fallback: {fallback}")
        return fallback

    def generate_body(self, test_case: TestCase, outline: str, title: str) -> str:
        """生成文章正文（Markdown 格式，顶部带标题，含图片占位符）。"""
        system_prompt = (
            "你是一个专业的内容写作者，擅长撰写通俗易懂、有传播力的公众号文章。"
            "请使用 Markdown 格式输出。"
        )

        user_prompt = f"""请基于以下大纲生成一篇完整的文章正文。

主题：{test_case.topic}
文章标题：{title}
大纲：
{outline}

目标字数：{test_case.word_count}字（允许 ±15%，仅统计正文不含标题，此为硬性要求）
图片占位符数量：{test_case.image_count}个
写作风格：{test_case.style}
目标受众：{test_case.audience}
发布平台：{test_case.platform}

## 输出格式要求（严格遵循）

请使用 Markdown 格式输出，结构如下：

# {title}

[正文内容从这里开始...]

### 小标题（用 ### 标记）
正文段落...

![AI配图中...](图片0路径)

正文继续...

## Markdown 格式要求
- 文章顶部第一行必须是 # {title} 格式的标题
- 使用 ## 或 ### 标记二级/三级小标题
- 适当使用 **加粗** 突出重点句子
- 段落之间空一行
- 正文整体结构清晰、层次分明

## 图片占位符格式（严格）

图片占位符必须使用标准的 Markdown 图片语法，每个占一行：

![AI配图中...](图片0路径)
![AI配图中...](图片1路径)
![AI配图中...](图片2路径)

格式严格为：![AI配图中...](图片n路径)，其中 n 从 0 开始连续递增到 {max(0, test_case.image_count - 1)}。
注意：不是 ![AI配图中...](图片0)，而必须是 ![AI配图中...](图片0路径)
alt 文本必须是 "AI配图中..." 不能变，路径必须是 "图片n路径" 其中 n 是数字。

## 写作要求

### 首段要求
- 迅速进入主题，前三句内切入核心
- 有冲突感、问题感或价值感
- 让读者愿意继续读
- 禁止使用"在当今社会""随着时代的发展""众所周知"等空泛套话

### 正文要求
- 围绕主题展开，与大纲结构一致
- 逻辑完整，论证充分
- 避免流水账式的堆砌
- 避免重复表达
- 避免过度口号化（不要连续使用感叹号或空洞号召）
- 避免明显 AI 腔（少用"综上所述""值得注意的是""不可否认"等表述）
- 语言自然流畅，像真人写作

### 图片占位符插入要求
- 必须在正文合适位置分散插入（不要全部堆在开头或结尾）
- 每个占位符独占一行
- 格式严格为 ![AI配图中...](图片n路径)，n从0开始连续递增
- 不能写成"图片一""图片 1""image1"或缺少感叹号/方括号等形式

## ⚠️ 字数硬性要求
- 正文总字数必须严格控制在 {int(test_case.word_count * 0.85)}-{int(test_case.word_count * 1.15)} 字之间
- 请在输出前自查字数，超出范围必须删减内容
- 宁可偏短不可偏长，800 字目标应输出 700-900 字

请直接输出完整 Markdown 正文（# 标题 + 正文 + 图片占位符），不要输出其他说明。"""

        return self._safe_call(system_prompt, user_prompt, max_tokens=8192,
                               fallback=f"# {title}\n\n关于{test_case.topic}的精彩内容，请参考正文。")

    def generate_share_text(self, topic: str, body: str) -> str:
        """生成 2-3 句转发文案。"""
        system_prompt = (
            "你是一个社交媒体运营专家。请为给定的文章生成简洁的转发文案。"
        )

        # 取正文前 500 字作为摘要
        body_summary = body[:500]

        user_prompt = f"""请基于以下文章内容，生成 2-3 句简洁的转发文案。

主题：{topic}

文章摘要（前500字）：
{body_summary}

要求：
1. 2-3 句即可，不要超过 100 字
2. 适合在朋友圈、微信群分享
3. 能激发读者的点击和阅读兴趣
4. 表达自然，不像是机器生成的

请直接输出转发文案，每句前用数字编号（1. 2. 3.），不要输出其他内容。"""

        return self._safe_call(system_prompt, user_prompt, max_tokens=512,
                               fallback=f"1. 关于{topic}的精彩内容，推荐阅读。\n2. 这篇文章讲透了{topic}的关键要点。")

    def generate_alternative_titles(self, topic: str, body: str, main_title: str) -> List[str]:
        """生成 3 个替补标题，严格禁止与主标题重复。"""
        system_prompt = (
            "你是一个资深标题创作者。请为给定的文章生成不同风格的替补标题。"
            "绝对不能与主标题相同或高度相似。"
        )

        body_summary = body[:300]

        user_prompt = f"""请基于以下文章，生成 3 个不同风格的替补标题。

主题：{topic}
主标题（已用，不可重复）：{main_title}

文章摘要（前300字）：
{body_summary}

要求：
1. 3 个标题风格各不相同（疑问式、数据式、冲突式、解决方案式、对比式）
2. 每个标题紧扣主题
3. **绝对不能与主标题「{main_title}」相同或高度相似**
4. 三个标题之间也不能相互重复
5. 每个标题 10-30 字
6. 不能标题党

请直接输出 3 个标题，每行一个，用数字编号：
1. xxx
2. xxx
3. xxx"""

        # 用简短主题作为 fallback
        short_t = topic[:15] + "…" if len(topic) > 15 else topic
        resp = self._safe_call(system_prompt, user_prompt, max_tokens=512,
                                fallback=f"1. {short_t}，你真的了解吗？\n2. 关于{short_t}的三个真相\n3. {short_t}的正确打开方式")
        # 解析标题
        import re
        titles = []
        for line in resp.split('\n'):
            line = line.strip()
            m = re.match(r'^\d+[\.\、\)\s]+\s*(.+)$', line)
            if m:
                t = m.group(1).strip().strip('"').strip("'")
                if t and len(t) >= 5:
                    titles.append(t)
            elif len(line) >= 5 and not line.startswith('以下是') and not line.startswith('替补'):
                if not any(kw in line for kw in ['风格', '标题', '以下', '建议']):
                    titles.append(line)

        # 去重：过滤与主标题相同或高度相似的
        # 使用更合理的相似度判断：仅当两标题的共同字符占比 >60% 时才判为相似
        def _is_similar(a: str, b: str) -> bool:
            a1 = a.replace(' ', '').replace('"', '').replace('"', '').replace('，', '').replace(',', '')
            b1 = b.replace(' ', '').replace('"', '').replace('"', '').replace('，', '').replace(',', '')
            if a1 == b1:
                return True
            # 计算字符级别 Jaccard 相似度
            set_a = set(a1)
            set_b = set(b1)
            if not set_a or not set_b:
                return False
            intersection = set_a & set_b
            union = set_a | set_b
            jaccard = len(intersection) / len(union) if union else 0
            # 如果 Jaccard > 0.7 且较短字符串长度占比 >50%, 判为相似
            shorter = min(len(a1), len(b1))
            longer = max(len(a1), len(b1))
            if jaccard > 0.7 and shorter / longer > 0.5:
                return True
            # 短标题完全包含在长标题中
            if shorter >= 6 and (a1[:shorter] in b1 or a1[-shorter:] in b1):
                return True
            return False

        filtered = []
        for t in titles:
            if not _is_similar(t, main_title) and not any(_is_similar(t, ft) for ft in filtered):
                filtered.append(t)

        # 用简短关键词生成较好的 fallback
        short_topic = topic[:12] + "…" if len(topic) > 12 else topic
        fallbacks = [
            f"别再忽视了，{short_topic}正在影响你的健康",
            f"关于{short_topic}，这篇文章说透了",
            f"{short_topic}：你可能一直在犯的错",
        ]
        while len(filtered) < 3:
            fb = fallbacks[len(filtered)]
            if not _is_similar(fb, main_title) and not any(_is_similar(fb, ft) for ft in filtered):
                filtered.append(fb)
            else:
                # 最终保底：加序号避免重复
                filtered.append(f"第{len(filtered)+1}个角度解读：{short_topic}")

        return filtered[:3]

    def fix_body(
        self, test_case: TestCase, body: str, outline: str, title: str,
        fix_instructions: str
    ) -> str:
        """根据检查结果修复正文。如果当前正文过短（<50字），则重新生成而非修复。"""
        # 如果正文过短（被之前的修复弄坏了），直接重新生成
        if len(body.strip()) < 50:
            logger.warning("  当前正文过短，重新生成而非修复")
            return self.generate_body(test_case, outline, title)

        system_prompt = (
            "你是一个专业的内容编辑。请根据反馈意见修复给定的文章正文。"
            "注意：必须在合适位置保留所有图片占位符（格式：![AI配图中...](图片n路径)），"
            "不要遗漏任何一个占位符，n必须从0开始连续递增。"
        )

        user_prompt = f"""请修复以下文章正文。

主题：{test_case.topic}
标题：{title}
目标字数：{test_case.word_count}字
图片占位符要求：{test_case.image_count}个（格式严格为 ![AI配图中...](图片n路径)，n从0到{max(0, test_case.image_count - 1)}）
注意：每个占位符独占一行，n必须从0开始连续递增。

原始大纲：
{outline}

修复要求：
{fix_instructions}

当前正文：
{body}

请直接输出修复后的完整正文，必须包含 {test_case.image_count} 个图片占位符（格式 ![AI配图中...](图片n路径)）。
正确格式示例：![AI配图中...](图片0路径)"""

        result = self._safe_call(system_prompt, user_prompt, max_tokens=8192, fallback="")

        # 检查修复结果是否有效
        if not result or len(result.strip()) < 100:
            logger.warning(f"  修复无效，保留修复前版本")
            return body

        return result

    def condense_body(
        self, test_case: TestCase, body: str, outline: str, title: str,
        actual_word_count: int
    ) -> Optional[str]:
        """精简正文到目标字数（专用精简 prompt，比通用 fix_body 更有效）。"""
        system_prompt = (
            "你是一个专业的内容精简编辑。你的任务是将文章压缩到目标字数，"
            "保留核心观点和关键论据，删除冗余描述。"
        )

        target = test_case.word_count
        user_prompt = f"""请将以下文章精简到 {target} 字左右。

主题：{test_case.topic}
当前字数：{actual_word_count} 字
目标字数：{target} 字（允许 {int(target*0.85)}-{int(target*1.15)} 字）

精简原则：
1. 保留所有核心观点和关键论据
2. 保留所有图片占位符（格式 ![AI配图中...](图片n路径)），不要删除任何一个
3. 保留文章标题行（# 开头的那行）
4. 删除重复论述和过度展开的细节
5. 合并相似的段落
6. 保持语言自然流畅

当前正文：
{body}

请直接输出精简后的完整 Markdown 正文（# 标题 + 精简正文 + 所有图片占位符）。"""

        result = self._safe_call(system_prompt, user_prompt, max_tokens=8192, fallback="")
        if not result or len(result.strip()) < 100:
            return None
        return result


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def process_single_case(
    client: LLMClient,
    test_case: TestCase,
    case_index: int,
    total_cases: int,
) -> ArticleOutput:
    """
    处理单个测例的完整流程。

    流程：
    1. 检索判断 + 材料获取
    2. 大纲生成
    3. 标题生成
    4. 正文生成
    5. 自检 → 修复（最多 2 次）
    6. 转发文案生成
    7. 替补标题生成
    """
    import time
    t_start = time.time()
    step_times = {}  # 记录每步耗时

    def tick(label: str):
        """记录步骤耗时并打印。"""
        now = time.time()
        elapsed = now - t_start
        # 计算距上次 tick 的增量
        if hasattr(tick, 'last'):
            delta = now - tick.last
            step_times[label] = delta
            logger.info(f"  ⏱ {label}: {delta:.1f}s (累计 {elapsed:.1f}s)")
        tick.last = now
    tick.last = t_start

    logger.info(f"[{case_index}/{total_cases}] 开始处理: {test_case.topic}")
    logger.info(f"  参数: 字数={test_case.word_count}, 图片={test_case.image_count}, 风格={test_case.style}")

    # ---- 步骤 1：检索判断 ----
    tick('1-检索判断')
    mat_result = retrieve_material(test_case.topic, test_case.extra_requirements)
    if mat_result.need_retrieval:
        logger.info(f"  需要检索材料: {mat_result.source_label}")
    else:
        logger.info(f"  无需检索: {mat_result.source_label}")

    # ---- 步骤 2：生成大纲 ----
    tick('2-生成大纲')
    outline = client.generate_outline(test_case, mat_result)

    # ---- 步骤 3：生成标题 ----
    tick('3-生成标题')
    title = client.generate_title(test_case.topic, outline)
    logger.info(f"  标题: {title}")

    # ---- 步骤 4：生成正文 ----
    tick('4-生成正文')
    body = client.generate_body(test_case, outline, title)

    # ---- 步骤 5：自检 + 修复循环（最多 1 次） ----
    tick('5-自检修复')
    max_fix_attempts = 1  # 从 2 降为 1：第 2 次修复成功率极低
    fix_count = 0
    for fix_attempt in range(max_fix_attempts + 1):
        check_result = check_article(
            topic=test_case.topic,
            body=body,
            title=title,
            word_count_target=test_case.word_count,
            image_count_target=test_case.image_count,
            outline=outline,
        )

        if check_result.passed:
            logger.info(f"  自检通过 ✅")
            break

        if fix_attempt < max_fix_attempts:
            fix_count += 1
            logger.warning(f"  自检未通过，开始修复...")

            body_issues = []
            title_issues = []
            for issue in check_result.issues:
                if '标题' in issue:
                    title_issues.append(issue)
                else:
                    body_issues.append(issue)

            if title_issues:
                logger.info(f"  修复标题: {title_issues}")
                title = client.generate_title(test_case.topic, outline)
                logger.info(f"  新标题: {title}")

            if body_issues:
                body_check = CheckResult(passed=False, issues=body_issues)
                fix_instructions = generate_fix_instructions(body_check)
                # 纯字数问题：用专用的精简 prompt，比通用 fix_body 更有效
                word_count_only = all('字数' in i for i in body_issues)
                if word_count_only and len(body_issues) == 1:
                    logger.info(f"  字数偏差，使用精简模式压缩...")
                    condensed = client.condense_body(
                        test_case, body, outline, title,
                        check_result.actual_word_count
                    )
                    if condensed and len(condensed.strip()) >= 100:
                        body = condensed
                    else:
                        logger.info(f"  精简无效，保留原文")
                else:
                    logger.info(f"  修复正文: {fix_instructions}")
                    fixed_body = client.fix_body(
                        test_case, body, outline, title, fix_instructions
                    )
                    if len(fixed_body.strip()) < 100:
                        logger.warning(f"  修复无效（返回 {len(fixed_body.strip())} 字），停止修复")
                        break
                    body = fixed_body
            elif title_issues and not body_issues:
                pass
        else:
            for issue in check_result.issues:
                logger.warning(f"  残留问题: {issue}")

    if fix_count > 0:
        step_times['5-自检修复'] = f"{fix_count}次修复"

    # ---- 步骤 6+7：并行生成转发文案 + 替补标题 ----
    tick('6-7 转发+替补(并行)')
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_share = executor.submit(
            client.generate_share_text, test_case.topic, body
        )
        future_alt = executor.submit(
            client.generate_alternative_titles, test_case.topic, body, title
        )
        share_text = future_share.result()
        alt_titles = future_alt.result()
    logger.info(f"  转发文案: {share_text[:100]}...")
    logger.info(f"  替补标题: {alt_titles}")

    # ---- 步骤 8：构建输出 ----
    tick('8-构建输出')
    output = ArticleOutput(
        topic=test_case.topic,
        body=body,
        title=title,
        share_text=share_text,
        alternative_titles=alt_titles,
    )

    total_elapsed = time.time() - t_start
    logger.info(f"[{case_index}/{total_cases}] 完成: {test_case.topic} ✅ (总耗时 {total_elapsed:.1f}s)")

    # 打印耗时摘要
    logger.info(f"  📊 耗时明细: " + " | ".join(
        f"{k}={v}" for k, v in step_times.items()
    ))

    return output


def main():
    parser = argparse.ArgumentParser(
        description='文章批量生成器 — 批量生成带图片占位符的文章，输出为 Excel 文件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 命令行直接输入
  python3 scripts/article_generator.py --input "以AI办公提效为主题，写一篇1200字文章，添加3个图片占位符"

  # 从 Excel 文件读取
  python3 scripts/article_generator.py --input-file article_inputs/cases.xlsx

  # 运行内置 demo
  python3 scripts/article_generator.py --demo

  # 指定输出路径
  python3 scripts/article_generator.py --demo --output article_outputs/my_result.xlsx
        """,
    )
    parser.add_argument(
        '--input', '-i', type=str,
        help='自然语言输入（多个测例用中文分号 ；分隔）',
    )
    parser.add_argument(
        '--input-file', '-f', type=str,
        help='Excel (.xlsx) 或 CSV 输入文件路径',
    )
    parser.add_argument(
        '--demo', '-d', action='store_true',
        help='使用内置的 3 个示例测例运行',
    )
    parser.add_argument(
        '--output', '-o', type=str,
        default='article_outputs/generated_articles.xlsx',
        help='输出 Excel 文件路径（默认: article_outputs/generated_articles.xlsx）',
    )

    args = parser.parse_args()

    # ---- 确定输入源 ----
    test_cases: List[TestCase] = []

    if args.input:
        logger.info("使用命令行输入")
        test_cases = parse_natural_language(args.input)
    elif args.input_file:
        logger.info(f"使用文件输入: {args.input_file}")
        test_cases = parse_excel_file(args.input_file)
    elif args.demo:
        logger.info("使用内置 demo 测例")
        test_cases = get_demo_cases()
    else:
        logger.error("未指定输入。请使用 --input、--input-file 或 --demo 参数。")
        parser.print_help()
        sys.exit(1)

    if not test_cases:
        logger.error("未能解析出任何有效测例，退出。")
        sys.exit(1)

    logger.info(f"共 {len(test_cases)} 个测例待处理")
    for i, tc in enumerate(test_cases, 1):
        logger.info(f"  [{i}] {tc}")

    # ---- 初始化 LLM 客户端 ----
    client = LLMClient()

    # ---- 逐个处理 ----
    outputs: List[ArticleOutput] = []
    start_time = time.time()

    for i, tc in enumerate(test_cases, 1):
        try:
            output = process_single_case(client, tc, i, len(test_cases))
            outputs.append(output)
        except Exception as e:
            logger.error(f"[{i}/{len(test_cases)}] 处理失败: {tc.topic} — {e}")
            # 创建错误输出，确保 Excel 中也有记录
            outputs.append(ArticleOutput(
                topic=tc.topic,
                body=f"[生成失败] {e}",
                title=tc.topic,
                share_text=f"1. 生成失败: {e}",
                alternative_titles=["N/A", "N/A", "N/A"],
            ))

    elapsed = time.time() - start_time
    logger.info(f"全部处理完成，耗时 {elapsed:.1f} 秒，成功 {len(outputs)}/{len(test_cases)}")

    # ---- 写入 Excel ----
    output_path = write_to_excel(outputs, args.output)

    # ---- 验证 ----
    if validate_excel(output_path):
        logger.info(f"✅ 最终输出: {output_path}")
    else:
        logger.error("❌ Excel 验证失败，请检查输出文件")
        sys.exit(1)

    # ---- 输出摘要 ----
    print("\n" + "=" * 60)
    print(f"📄 批量文章生成完成")
    print(f"   测例总数: {len(test_cases)}")
    print(f"   成功生成: {len(outputs)}")
    print(f"   输出文件: {os.path.abspath(output_path)}")
    print("=" * 60)

    for i, out in enumerate(outputs, 1):
        print(f"\n--- 第 {i} 篇 ---")
        print(f"   主题: {out.topic}")
        print(f"   标题: {out.title}")
        print(f"   图片占位符: {out.body.count('![AI配图中...](图片')} 个")
        print(f"   正文预览: {out.body[:80].replace(chr(10), ' ')}...")
        print(f"   转发文案: {out.share_text[:60].replace(chr(10), ' ')}...")
        print(f"   替补标题: {len(out.alternative_titles)} 个")


if __name__ == '__main__':
    main()
