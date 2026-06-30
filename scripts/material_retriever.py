#!/usr/bin/env python3
"""
材料检索模块 — 判断是否需要检索外部材料，并执行检索（当前为 mock 实现）。

设计原则：
  - 检索判断逻辑独立，基于关键词和主题类型
  - 检索实现可插拔（通过 SearchProvider 抽象接口）
  - 当前提供 MockSearchProvider，未来可接入真实搜索 API
  - 如果无法联网检索，在结果中标注"未检索外部材料，基于通用知识生成"
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, Protocol, List
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------

@dataclass
class MaterialResult:
    """检索结果。"""
    need_retrieval: bool = False
    retrieved: bool = False
    source_label: str = ""                # 材料来源说明
    materials: str = ""                   # 整理后的材料要点
    search_queries: List[str] = field(default_factory=list)  # 建议的搜索词


# ---------------------------------------------------------------------------
# 检索判断
# ---------------------------------------------------------------------------

# 触发检索的关键词
RETRIEVAL_KEYWORDS = [
    # 时间相关
    '最新', '近期', '最近', '今年', '本月', '上月', '上周',
    '2024', '2025', '2026', '2023',
    # 政策法规
    '政策', '法规', '规定', '监管', '政府', '国务院', '工信部',
    '出台', '新规', '新政',
    # 市场数据
    '数据', '报告', '统计', '趋势', '市场', '份额', '增长',
    '下降', '营收', '利润',
    # 公司/产品
    '财报', '融资', '上市', '收购', '合并', '裁员', '扩张',
    '发布', '新品', '版本', '更新', '迭代',
    # 事件
    '事件', '热点', '新闻',
    # 行业技术
    '技术突破', '新技术', '行业趋势', '白皮书',
]


def should_retrieve_material(topic: str, extra_requirements: str = "") -> bool:
    """
    判断是否需要检索外部材料。

    判断逻辑：
    - 如果主题/要求中包含时间敏感词、政策词、数据词、公司/产品词 → 需要检索
    - 如果主题是常识性、经验型、观点型 → 不需要检索

    返回 True 表示需要检索，False 表示可直接生成。
    """
    combined = f"{topic} {extra_requirements}".lower()

    for kw in RETRIEVAL_KEYWORDS:
        if kw.lower() in combined:
            logger.info(f"触发检索判断: 主题包含关键词 '{kw}' → 需要检索材料")
            return True

    logger.info(f"检索判断: 主题 '{topic}' 不需要检索外部材料")
    return False


def get_suggested_queries(topic: str) -> List[str]:
    """根据主题生成建议的搜索查询词。"""
    queries = [
        f"{topic} 最新进展",
        f"{topic} 行业趋势",
        f"{topic} 数据报告",
    ]
    return queries


# ---------------------------------------------------------------------------
# 可插拔检索接口
# ---------------------------------------------------------------------------

class SearchProvider(ABC):
    """搜索服务抽象接口。未来可接入真实搜索 API。"""

    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> List[dict]:
        """
        执行搜索。

        参数:
            query: 搜索关键词
            max_results: 最大结果数

        返回:
            List[dict]，每个 dict 包含：
            - title: 标题
            - snippet: 摘要
            - url: 链接
            - source: 来源
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """搜索服务名称。"""
        ...


class MockSearchProvider(SearchProvider):
    """
    Mock 搜索服务 — 返回模拟结果。

    用于开发测试阶段，或无法联网时。
    返回的 mock 数据基于通用知识组织，非真实检索结果。
    """

    @property
    def name(self) -> str:
        return "MockSearchProvider"

    def search(self, query: str, max_results: int = 5) -> List[dict]:
        """返回模拟搜索结果。"""
        logger.info(f"MockSearch: 模拟搜索 '{query}'")

        # 通用 mock 结果
        mock_results = [
            {
                'title': f'「{query}」相关行业分析',
                'snippet': f'关于{query}的行业发展现状与未来趋势的综合分析...',
                'url': 'https://example.com/mock-1',
                'source': 'Mock数据源',
            },
            {
                'title': f'{query} — 最新解读与观点',
                'snippet': f'多位行业专家对{query}的最新观点和深度解读...',
                'url': 'https://example.com/mock-2',
                'source': 'Mock数据源',
            },
            {
                'title': f'{query}实践案例汇编',
                'snippet': f'收集了{query}在多个行业的落地实践案例...',
                'url': 'https://example.com/mock-3',
                'source': 'Mock数据源',
            },
        ]
        return mock_results[:max_results]


# ---------------------------------------------------------------------------
# 材料检索主函数
# ---------------------------------------------------------------------------

def retrieve_material(
    topic: str,
    extra_requirements: str = "",
    search_provider: Optional[SearchProvider] = None,
) -> MaterialResult:
    """
    检索材料的主入口。

    流程：
    1. 判断是否需要检索
    2. 如需要，调用搜索服务获取材料
    3. 整理材料为要点文本

    参数:
        topic: 文章主题
        extra_requirements: 额外要求
        search_provider: 搜索服务实例，默认使用 MockSearchProvider

    返回:
        MaterialResult
    """
    need = should_retrieve_material(topic, extra_requirements)

    if not need:
        return MaterialResult(
            need_retrieval=False,
            retrieved=False,
            source_label="常识性/经验型主题，无需检索外部材料",
            materials="",
        )

    # 确定搜索服务
    if search_provider is None:
        search_provider = MockSearchProvider()

    # 生成搜索词
    queries = get_suggested_queries(topic)
    all_results = []

    for q in queries:
        try:
            results = search_provider.search(q)
            all_results.extend(results)
        except Exception as e:
            logger.warning(f"搜索 '{q}' 失败: {e}")
            continue

    # 去重
    seen_urls = set()
    unique_results = []
    for r in all_results:
        if r['url'] not in seen_urls:
            seen_urls.add(r['url'])
            unique_results.append(r)

    # 整理为材料要点
    materials_parts = []
    for i, r in enumerate(unique_results, 1):
        materials_parts.append(
            f"{i}. **{r['title']}**\n"
            f"   摘要：{r['snippet']}\n"
            f"   来源：{r['source']}"
        )

    materials_text = "\n\n".join(materials_parts) if materials_parts else ""

    # 判断是否实际检索到了材料
    is_mock = isinstance(search_provider, MockSearchProvider)
    if is_mock:
        source_label = "未检索外部材料，基于通用知识生成（Mock模式）"
    else:
        source_label = f"通过 {search_provider.name} 检索"

    return MaterialResult(
        need_retrieval=True,
        retrieved=len(unique_results) > 0,
        source_label=source_label,
        materials=materials_text,
        search_queries=queries,
    )
