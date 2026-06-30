"""
操作注册表 — 统一管理所有图像操作。

设计原则：
- 所有操作实现统一接口
- 每个操作自带 JSON Schema（直接给 LLM 做 Function Calling）
- 单例模式，避免重复注册
"""

from typing import Dict, List, Type, Any
import logging

logger = logging.getLogger(__name__)


class ImageOperation:
    """
    图像操作抽象基类。

    所有操作必须实现：
    - execute(image, params) → image
    - get_schema() → dict (JSON Schema for LLM)
    """

    name: str = ""
    description: str = ""

    def execute(self, image: "np.ndarray", params: dict) -> "np.ndarray":
        """执行操作，返回处理后的图像。"""
        raise NotImplementedError

    def get_schema(self) -> dict:
        """返回 Function Calling Schema。"""
        raise NotImplementedError

    def to_function_definition(self) -> dict:
        """生成 Anthropic tool 格式的定义。"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.get_schema(),
        }


class OperationRegistry:
    """
    操作注册表 — 单例。

    用法:
        registry = OperationRegistry()
        registry.register(AdjustBrightness())

        # 获取所有操作的 Function Calling schema
        tools = registry.get_tool_definitions()

        # 执行操作
        result = registry.execute("adjust_brightness", image, {"value": 15})
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._operations: Dict[str, ImageOperation] = {}
            cls._instance._initialized = False
        return cls._instance

    def register(self, operation: ImageOperation) -> None:
        """注册一个操作。"""
        if operation.name in self._operations:
            logger.warning(f"操作 '{operation.name}' 已注册，将覆盖")
        self._operations[operation.name] = operation
        logger.debug(f"操作已注册: {operation.name}")

    def get(self, name: str) -> ImageOperation:
        """获取指定操作。"""
        if name not in self._operations:
            raise KeyError(f"未知操作: {name}。可用操作: {list(self._operations.keys())}")
        return self._operations[name]

    def list_operations(self) -> List[str]:
        """列出所有已注册操作名称。"""
        return list(self._operations.keys())

    def get_tool_definitions(self) -> List[dict]:
        """生成 Anthropic tool 格式的完整定义列表。"""
        return [
            {
                "type": "function",
                "function": op.to_function_definition(),
            }
            for op in self._operations.values()
        ]

    def get_operations_summary(self) -> str:
        """生成操作摘要文本（用于 System Prompt）。"""
        lines = []
        for name, op in self._operations.items():
            lines.append(f"- {name}: {op.description}")
        return "\n".join(lines)

    def execute(self, name: str, image: "np.ndarray", params: dict) -> "np.ndarray":
        """根据操作名执行操作。"""
        op = self.get(name)
        logger.info(f"执行操作: {name}({params})")
        return op.execute(image, params)

    @property
    def skill_executor(self):
        """获取 Skill 执行器（懒加载）。"""
        if not hasattr(self, '_skill_executor'):
            from image_engine.operations.skills import SkillExecutor, get_all_skill_schemas, get_skills_summary
            self._skill_executor = SkillExecutor(self)
            self._skill_schemas = get_all_skill_schemas()
            self._skills_summary = get_skills_summary()
        return self._skill_executor

    def get_skill_schemas(self) -> List[dict]:
        """获取所有 Skill 的 LLM Function Schema。"""
        self.skill_executor  # 触发加载
        return self._skill_schemas

    def get_skills_summary(self) -> str:
        """获取 Skills 摘要文本。"""
        self.skill_executor
        return self._skills_summary

    def execute_skill(self, name: str, image: "np.ndarray", params: dict) -> "np.ndarray":
        """执行一个 Skill。"""
        return self.skill_executor.execute(name, image, params)

    def init_all(self) -> "OperationRegistry":
        """注册所有内置操作。"""
        if self._initialized:
            return self

        from image_engine.operations.adjust import (
            AdjustBrightness, AdjustContrast, AdjustSaturation,
        )
        from image_engine.operations.transform import (
            Crop, Resize, Rotate, CropToSquare, Flip,
        )
        from image_engine.operations.filter import (
            GrayscaleFilter, SepiaFilter, BlurFilter, SharpenFilter,
        )
        from image_engine.operations.local_adjust import (
            LocalBrightness, LocalContrast, LocalSaturation,
            LocalSharpen, LocalBlur, DodgeOperation, BurnOperation,
        )

        self.register(AdjustBrightness())
        self.register(AdjustContrast())
        self.register(AdjustSaturation())
        self.register(Crop())
        self.register(CropToSquare())
        self.register(Resize())
        self.register(Rotate())
        self.register(Flip())
        self.register(GrayscaleFilter())
        self.register(SepiaFilter())
        self.register(BlurFilter())
        self.register(SharpenFilter())
        self.register(LocalBrightness())
        self.register(LocalContrast())
        self.register(LocalSaturation())
        self.register(LocalSharpen())
        self.register(LocalBlur())
        self.register(DodgeOperation())
        self.register(BurnOperation())

        self._initialized = True
        logger.info(f"已注册 {len(self._operations)} 个基础操作")
        # 触发 Skills 加载
        self.skill_executor
        logger.info(f"已加载 {len(self._skill_schemas)} 个高级 Skills")
        return self
