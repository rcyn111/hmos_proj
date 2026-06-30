"""
AI Commander — 将自然语言指令解析为操作调用链。

用法:
    commander = AICommander()
    calls = commander.parse("把图片调亮并裁成正方形")
    for call in calls:
        canvas.image = registry.execute(call.name, canvas.image, call.params)
"""

import json
import logging
import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from image_engine.operations.registry import OperationRegistry
from ai_commander.prompts import build_system_prompt

logger = logging.getLogger(__name__)


@dataclass
class OperationCall:
    """一次操作调用。"""
    name: str                          # 操作名，如 "adjust_brightness"
    params: Dict[str, Any] = field(default_factory=dict)
    description: str = ""              # 人类可读的描述


@dataclass
class CommandResult:
    """指令解析结果。"""
    success: bool
    calls: List[OperationCall] = field(default_factory=list)
    descriptions: List[str] = field(default_factory=list)  # 逐步描述
    raw_response: str = ""
    error: str = ""


class AICommander:
    """
    自然语言 → 图像操作链。

    工作流程:
    1. 接收用户自然语言输入
    2. 调用 LLM (Function Calling) 解析意图
    3. 提取函数调用链
    4. 验证参数合法性
    5. 依次调用底层引擎执行
    """

    def __init__(self, model: str = None):
        self.registry = OperationRegistry().init_all()

        # LLM 客户端
        self.base_url = os.environ.get(
            "ANTHROPIC_BASE_URL", "https://api.deepseek.com/anthropic"
        )
        self.api_key = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
        self.model = model or os.environ.get("ANTHROPIC_MODEL", "deepseek-v4-pro")

        if not self.api_key:
            logger.warning("未检测到 ANTHROPIC_AUTH_TOKEN，请设置环境变量")

        self._client = None
        self._image_context: Dict[str, Any] = {}

    @property
    def client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(
                base_url=self.base_url,
                api_key=self.api_key,
            )
        return self._client

    def set_image_context(self, width: int, height: int, format: str = "",
                          color_mode: str = "", image: "np.ndarray" = None) -> None:
        """设置当前图像的上下文信息（帮助 AI 做出更好的参数推断）。"""
        self._image_context = {
            "width": width,
            "height": height,
            "format": format,
            "color_mode": color_mode,
        }
        # 分析图像统计信息
        if image is not None:
            from image_engine.core.mask import analyze_image
            stats = analyze_image(image)
            self._image_stats = {
                "mean_brightness": round(stats.mean_brightness, 1),
                "dark_ratio": f"{stats.dark_ratio:.1%}",
                "bright_ratio": f"{stats.bright_ratio:.1%}",
                "has_sunlight": stats.has_sunlight,
                "has_shadow": stats.has_shadow,
                "dominant_colors": stats.dominant_colors,
            }
        else:
            self._image_stats = {}

    def parse(self, user_command: str) -> CommandResult:
        """
        解析用户自然语言指令。

        DSAPI 不支持原生 Function Calling，因此采用：
        System Prompt 嵌入函数 Schema → 要求 LLM 输出 JSON → 解析 JSON。

        参数:
            user_command: 用户输入的自然语言，如 "把图调亮一点，然后裁成正方形"

        返回:
            CommandResult 包含操作调用链
        """
        if not self.api_key:
            return CommandResult(
                success=False,
                error="未设置 ANTHROPIC_AUTH_TOKEN 环境变量，无法调用 AI 服务"
            )

        # 构建内嵌 Schema 的 System Prompt
        system_prompt = build_system_prompt(
            operations_summary=self.registry.get_operations_summary(),
            image_context=self._image_context,
            function_schemas=self._build_schema_text(),
            image_stats=self._image_stats,
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": user_command}],
            )
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            return CommandResult(success=False, error=f"AI 服务调用失败: {e}")

        # 提取文本并解析 JSON
        text = self._extract_text(response)
        logger.info(f"LLM 原始回复: {text[:300]}")

        calls = self._parse_json_calls(text)
        if not calls:
            return CommandResult(
                success=False,
                raw_response=text,
                error=f"AI 未输出有效的操作 JSON。回复: {text[:200]}"
            )

        descriptions = [
            f"{call.name}: {call.description}" if call.description else call.name
            for call in calls
        ]

        return CommandResult(
            success=True,
            calls=calls,
            descriptions=descriptions,
            raw_response=text,
        )

    def _build_schema_text(self) -> str:
        """将所有操作和 Skills 的 Schema 转为文本，嵌入 System Prompt。"""
        lines = []

        # 基础操作
        lines.append("## 🔧 基础操作\n")
        for name, op in self.registry._operations.items():
            schema = op.get_schema()
            props = schema.get("properties", {})
            required = schema.get("required", [])

            params_desc = []
            for pname, pinfo in props.items():
                req_mark = " (必填)" if pname in required else " (可选)"
                params_desc.append(f"      {pname}: {pinfo.get('type', 'any')}{req_mark} — {pinfo.get('description', '')}")

            lines.append(f"### {name}")
            lines.append(f"    说明: {op.description}")
            if params_desc:
                lines.append(f"    参数:")
                lines.extend(params_desc)
            lines.append(f"    JSON: {{\"action\": \"{name}\", \"params\": {{...}}}}")
            lines.append("")

        # Skills
        lines.append("## 🎯 高级 Skills（组合操作）\n")
        lines.append("Skills 是预制的多步操作组合，一个 Skill 内部会自动拆解为基础操作序列。")
        lines.append("优先使用 Skill 来完成复杂编辑需求。\n")
        for skill in self.registry.get_skill_schemas():
            lines.append(f"### {skill['name']}")
            lines.append(f"    说明: {skill['description']}")
            schema = skill['input_schema']
            props = schema.get('properties', {})
            required = schema.get('required', [])
            if props:
                lines.append("    参数:")
                for pname, pinfo in props.items():
                    req_mark = " (必填)" if pname in required else " (可选)"
                    lines.append(f"      {pname}: {pinfo['type']}{req_mark} — {pinfo['description']}")
            lines.append(f"    JSON: {{\"action\": \"{skill['name']}\", \"params\": {{...}}}}")
            lines.append("")

        return "\n".join(lines)

    def _parse_json_calls(self, text: str) -> List[OperationCall]:
        """从 LLM 文本回复中解析 JSON 操作调用。"""
        import re

        # 尝试匹配 JSON 数组: [{"action": "...", "params": {...}}, ...]
        # 或单个 JSON: {"action": "...", "params": {...}}
        calls = []

        # 提取所有 JSON 对象
        json_pattern = r'\{[^{}]*"action"\s*:\s*"[^"]+"\s*,\s*"params"\s*:\s*\{[^{}]*\}[^{}]*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)

        if not matches:
            # 尝试提取 JSON 代码块
            code_block = re.search(r'```(?:json)?\s*(\[.*?\]|\{.*?\})\s*```', text, re.DOTALL)
            if code_block:
                try:
                    parsed = json.loads(code_block.group(1))
                    if isinstance(parsed, list):
                        for item in parsed:
                            calls.append(OperationCall(
                                name=item.get("action", ""),
                                params=item.get("params", {}),
                                description=item.get("description", ""),
                            ))
                    elif isinstance(parsed, dict):
                        calls.append(OperationCall(
                            name=parsed.get("action", ""),
                            params=parsed.get("params", {}),
                            description=parsed.get("description", ""),
                        ))
                    return [c for c in calls if c.name]
                except json.JSONDecodeError:
                    pass

        for m in matches:
            try:
                obj = json.loads(m)
                if "action" in obj:
                    calls.append(OperationCall(
                        name=obj.get("action", ""),
                        params=obj.get("params", {}),
                        description=obj.get("description", ""),
                    ))
            except json.JSONDecodeError:
                continue

        # 如果以上都没匹配到，尝试更宽松的匹配
        if not calls:
            # 查找类似 "action": "xxx" 的模式
            action_matches = re.findall(r'"action"\s*:\s*"([^"]+)"', text)
            for i, action_name in enumerate(action_matches):
                if action_name in self.registry._operations:
                    # 尝试提取参数
                    params = {}
                    params_match = re.search(r'"params"\s*:\s*(\{[^}]+\})', text)
                    if params_match:
                        try:
                            params = json.loads(params_match.group(1))
                        except json.JSONDecodeError:
                            pass
                    calls.append(OperationCall(name=action_name, params=params))

        # 同时检查基础操作和 Skill 名称
        from image_engine.operations.skills import SKILL_LIBRARY
        valid_names = set(self.registry._operations.keys()) | set(SKILL_LIBRARY.keys())
        return [c for c in calls if c.name in valid_names]

    def execute(self, image: "np.ndarray", user_command: str,
                history=None) -> "np.ndarray":
        """
        一站式方法：解析指令并执行。支持基础操作和高级 Skills。

        参数:
            image: 当前图像 (numpy array)
            user_command: 用户指令
            history: HistoryManager 实例（可选，用于记录操作）

        返回:
            处理后的图像
        """
        # 更新上下文（含图像分析）
        h, w = image.shape[:2]
        self.set_image_context(width=w, height=h, image=image)

        # 解析
        result = self.parse(user_command)
        if not result.success:
            raise RuntimeError(f"指令解析失败: {result.error}")

        # 执行
        current = image
        for i, call in enumerate(result.calls):
            description = call.description or f"{call.name}({call.params})"
            logger.info(f"  [{i+1}/{len(result.calls)}] {description}")

            # 保存快照
            if history:
                history.save_snapshot(call.name, current, description)

            try:
                # 判断是 Skill 还是基础操作
                from image_engine.operations.skills import SKILL_LIBRARY
                if call.name in SKILL_LIBRARY:
                    current = self.registry.execute_skill(call.name, current, call.params)
                else:
                    current = self.registry.execute(call.name, current, call.params)
            except Exception as e:
                logger.error(f"操作执行失败: {call.name} — {e}")
                raise RuntimeError(f"执行 '{call.name}' 时出错: {e}")

        return current

    def _extract_calls(self, response) -> List[OperationCall]:
        """从 LLM 响应中提取 function calls。"""
        calls = []
        for block in response.content:
            if hasattr(block, 'type') and block.type == 'tool_use':
                params = block.input if isinstance(block.input, dict) else {}
                calls.append(OperationCall(
                    name=block.name,
                    params=params,
                    description=self._make_description(block.name, params),
                ))
        return calls

    def _extract_text(self, response) -> str:
        """从 LLM 响应中提取文本。"""
        texts = []
        for block in response.content:
            if hasattr(block, 'text'):
                texts.append(block.text)
        return '\n'.join(texts)

    def _make_description(self, name: str, params: dict) -> str:
        """生成人类可读的操作描述。"""
        desc_map = {
            "adjust_brightness": lambda p: f"亮度 {'+' if p.get('value',0) >= 0 else ''}{p.get('value',0)}",
            "adjust_contrast": lambda p: f"对比度 {'+' if p.get('value',0) >= 0 else ''}{p.get('value',0)}",
            "adjust_saturation": lambda p: f"饱和度 {'+' if p.get('value',0) >= 0 else ''}{p.get('value',0)}",
            "crop": lambda p: f"裁剪 {p.get('width','?')}x{p.get('height','?')}",
            "crop_to_square": lambda p: "裁剪为正方形",
            "resize": lambda p: f"缩放至 {p.get('width','?')}x{p.get('height','?')}" if p.get('width') or p.get('height') else f"缩放 {p.get('scale','?')}x",
            "rotate": lambda p: f"旋转 {p.get('angle',0)}°",
            "apply_grayscale": lambda p: "转为黑白",
            "apply_sepia": lambda p: f"复古效果 {p.get('intensity',70)}%",
            "apply_blur": lambda p: f"模糊强度 {p.get('strength',10)}",
            "apply_sharpen": lambda p: f"锐化强度 {p.get('strength',50)}",
        }
        fn = desc_map.get(name, lambda p: f"{name}({p})")
        return fn(params)
