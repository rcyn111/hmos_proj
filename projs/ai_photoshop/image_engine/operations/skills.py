"""
Skills Set — 高级组合操作。

Skill 是一组基础操作的配方（recipe），AI 可以像调用基础函数一样调用 Skill。
每个 Skill 内部拆解为多个基础操作 + 蒙版，AI 也可以自由组合基础操作来应对未知需求。

设计原则：
- Skill 有明确的名称、描述、适用场景
- Skill 内部实现用基础操作 + 蒙版组合
- 参数设计简单，用户/LLM 不必了解内部细节
"""

import cv2
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from image_engine.core.mask import Mask


# ====================================================================
# Skill 定义
# ====================================================================

@dataclass
class SkillDefinition:
    """一个 Skill 的元数据定义。"""
    name: str
    description: str                    # 一句话描述
    when_to_use: str                    # 什么时候用
    parameters: List[Dict[str, Any]]    # 参数列表
    example: str                        # 使用示例


# ====================================================================
# 所有 Skills 注册
# ====================================================================

SKILL_LIBRARY: Dict[str, SkillDefinition] = {}


def register_skill(name: str, description: str, when_to_use: str,
                   parameters: List[Dict], example: str):
    """注册一个 Skill。"""
    SKILL_LIBRARY[name] = SkillDefinition(
        name=name,
        description=description,
        when_to_use=when_to_use,
        parameters=parameters,
        example=example,
    )


# ---- 光影控制类 ----

register_skill(
    name="brighten_subject",
    description="提亮画面主体/中心区域，压暗四周",
    when_to_use="用户说'让主体更突出''压暗背景''突出中间''聚光效果'时使用",
    parameters=[
        {"name": "brighten_amount", "type": "int", "range": [5, 50], "default": 20,
         "description": "主体提亮强度"},
        {"name": "darken_amount", "type": "int", "range": [5, 40], "default": 15,
         "description": "四周压暗强度"},
    ],
    example="用户: '让中间更亮一点' → brighten_subject(brighten_amount=20, darken_amount=10)"
)

register_skill(
    name="enhance_sunlight",
    description="增强画面中的阳光/高光区域，加深阴影",
    when_to_use="用户说'让阳光更亮''高光更强''光影对比更强''增加阳光感'时使用",
    parameters=[
        {"name": "highlight_boost", "type": "int", "range": [10, 60], "default": 30,
         "description": "高光增强强度"},
        {"name": "shadow_deepen", "type": "int", "range": [5, 40], "default": 15,
         "description": "阴影加深强度"},
    ],
    example="用户: '让阳光更强烈一点' → enhance_sunlight(highlight_boost=35, shadow_deepen=15)"
)

register_skill(
    name="fix_underexposed",
    description="修复暗部/曝光不足的区域",
    when_to_use="用户说'暗部太黑了''脸太暗''逆光''阴影太重'时使用",
    parameters=[
        {"name": "brighten_amount", "type": "int", "range": [10, 60], "default": 30,
         "description": "暗部提亮强度"},
    ],
    example="用户: '暗部太黑了' → fix_underexposed(brighten_amount=30)"
)

register_skill(
    name="reduce_highlights",
    description="压低过曝/高光区域，保留细节",
    when_to_use="用户说'太亮了''过曝''高光溢出''白色太刺眼'时使用",
    parameters=[
        {"name": "darken_amount", "type": "int", "range": [10, 50], "default": 25,
         "description": "高光压低强度"},
    ],
    example="用户: '天空太白了' → reduce_highlights(darken_amount=25)"
)

register_skill(
    name="dodge_and_burn",
    description="经典减淡加深：提亮特定区域，加深其他区域，增强立体感",
    when_to_use="用户说'增加立体感''减淡加深''加强层次'时使用",
    parameters=[
        {"name": "dodge_amount", "type": "int", "range": [5, 30], "default": 15,
         "description": "减淡（提亮）强度"},
        {"name": "burn_amount", "type": "int", "range": [5, 30], "default": 15,
         "description": "加深（压暗）强度"},
    ],
    example="用户: '增加立体感' → dodge_and_burn(dodge_amount=15, burn_amount=15)"
)

# ---- 色彩氛围类 ----

register_skill(
    name="golden_hour",
    description="模拟黄金时刻暖光效果",
    when_to_use="用户说'金色阳光''黄昏感''暖光''黄金时刻''日落色调'时使用",
    parameters=[
        {"name": "intensity", "type": "int", "range": [20, 100], "default": 60,
         "description": "效果强度"},
    ],
    example="用户: '加一点金色阳光的感觉' → golden_hour(intensity=50)"
)

register_skill(
    name="moody_cool",
    description="冷色调忧郁氛围",
    when_to_use="用户说'冷色调''忧郁感''电影感冷色''清冷'时使用",
    parameters=[
        {"name": "intensity", "type": "int", "range": [20, 100], "default": 50,
         "description": "效果强度"},
    ],
    example="用户: '冷色调一点' → moody_cool(intensity=40)"
)

register_skill(
    name="vibrant_pop",
    description="增加鲜艳度和对比度，让颜色更'跳'",
    when_to_use="用户说'颜色更跳''鲜艳一点但不失真''色彩更饱满'时使用",
    parameters=[
        {"name": "intensity", "type": "int", "range": [10, 60], "default": 30,
         "description": "增强强度"},
    ],
    example="用户: '让颜色更跳一点' → vibrant_pop(intensity=25)"
)

# ---- 肖像/人物类 ----

register_skill(
    name="skin_smooth",
    description="轻微磨皮柔化肤色",
    when_to_use="用户说'磨皮''皮肤光滑一点''柔肤'时使用",
    parameters=[
        {"name": "strength", "type": "int", "range": [3, 20], "default": 8,
         "description": "磨皮强度，值越大越光滑"},
    ],
    example="用户: '皮肤光滑一点' → skin_smooth(strength=8)"
)

register_skill(
    name="eye_enhance",
    description="增强眼睛清晰度和亮度（需配合脸部选区）",
    when_to_use="用户说'眼睛亮一点''眼睛更清晰''眼神光'时使用",
    parameters=[
        {"name": "strength", "type": "int", "range": [5, 30], "default": 15,
         "description": "增强强度"},
    ],
    example="用户: '眼睛亮一点' → eye_enhance(strength=15)"
)

# ---- 构图/效果类 ----

register_skill(
    name="add_vignette",
    description="添加暗角效果，引导视线到画面中心",
    when_to_use="用户说'暗角''四周暗一点''引导视线''聚焦中心'时使用",
    parameters=[
        {"name": "intensity", "type": "int", "range": [10, 80], "default": 40,
         "description": "暗角强度"},
    ],
    example="用户: '加个暗角' → add_vignette(intensity=40)"
)

register_skill(
    name="clarity_boost",
    description="增加画面清晰度和纹理（类似 PS 的 Clarity 滑块）",
    when_to_use="用户说'更清晰''增加质感''锐化但不要太假'时使用",
    parameters=[
        {"name": "strength", "type": "int", "range": [10, 60], "default": 30,
         "description": "清晰度增强强度"},
    ],
    example="用户: '质感强一点' → clarity_boost(strength=30)"
)


# ====================================================================
# Skill 执行器
# ====================================================================

class SkillExecutor:
    """
    执行 Skill — 将 Skill 拆解为基础操作序列并依次执行。

    Skill 内部实现可以调用任何基础操作和蒙版操作。
    """

    def __init__(self, registry):
        self.registry = registry  # OperationRegistry 实例

    def execute(self, skill_name: str, image: np.ndarray,
                params: Dict[str, Any]) -> np.ndarray:
        """执行一个 Skill，返回处理后的图像。"""
        method_name = f"_exec_{skill_name}"
        if not hasattr(self, method_name):
            raise ValueError(f"未知 Skill: {skill_name}。可用: {list(SKILL_LIBRARY.keys())}")

        executor = getattr(self, method_name)
        return executor(image, params)

    # ---- 光影控制 ----

    def _exec_brighten_subject(self, image: np.ndarray, p: dict) -> np.ndarray:
        brighten = p.get("brighten_amount", 20)
        darken = p.get("darken_amount", 15)

        h, w = image.shape[:2]
        # 中心椭圆蒙版
        center_mask = Mask.from_ellipse(image.shape, w//2, h//2, w//3, h//3)
        center_mask.feather(radius=max(w, h) // 15)

        # 提亮中心
        brightened = self.registry.execute("adjust_brightness", image, {"value": brighten})
        result = center_mask.apply(image, brightened)

        # 压暗四周（反转蒙版）
        edge_mask = Mask(center_mask.data.copy()).invert()
        darkened = self.registry.execute("adjust_brightness", result, {"value": -darken})
        result = edge_mask.apply(result, darkened)

        return result

    def _exec_enhance_sunlight(self, image: np.ndarray, p: dict) -> np.ndarray:
        highlight = p.get("highlight_boost", 30)
        shadow = p.get("shadow_deepen", 15)

        # 亮部蒙版
        light_mask = Mask.from_brightness_range(image, min_val=150, max_val=255)
        light_mask.feather(radius=15)

        # 暗部蒙版
        dark_mask = Mask.from_brightness_range(image, min_val=0, max_val=100)
        dark_mask.feather(radius=15)

        # 提亮高光
        brightened = self.registry.execute("adjust_brightness", image, {"value": highlight})
        result = light_mask.apply(image, brightened)

        # 加深阴影
        darkened = self.registry.execute("adjust_brightness", result, {"value": -shadow})
        result = dark_mask.apply(result, darkened)

        # 加一点暖色让阳光更明显
        result = self.registry.execute("adjust_saturation", result, {"value": 10})

        return result

    def _exec_fix_underexposed(self, image: np.ndarray, p: dict) -> np.ndarray:
        brighten = p.get("brighten_amount", 30)

        dark_mask = Mask.from_brightness_range(image, min_val=0, max_val=100)
        dark_mask.feather(radius=20)

        brightened = self.registry.execute("adjust_brightness", image, {"value": brighten})
        return dark_mask.apply(image, brightened)

    def _exec_reduce_highlights(self, image: np.ndarray, p: dict) -> np.ndarray:
        darken = p.get("darken_amount", 25)

        light_mask = Mask.from_brightness_range(image, min_val=200, max_val=255)
        light_mask.feather(radius=15)

        darkened = self.registry.execute("adjust_brightness", image, {"value": -darken})
        return light_mask.apply(image, darkened)

    def _exec_dodge_and_burn(self, image: np.ndarray, p: dict) -> np.ndarray:
        dodge = p.get("dodge_amount", 15)
        burn = p.get("burn_amount", 15)

        # 减淡：提亮中亮区域
        light_mask = Mask.from_brightness_range(image, min_val=120, max_val=200)
        light_mask.feather(radius=10)
        brightened = self.registry.execute("adjust_brightness", image, {"value": dodge})
        result = light_mask.apply(image, brightened)

        # 加深：压暗暗部
        dark_mask = Mask.from_brightness_range(result, min_val=0, max_val=120)
        dark_mask.feather(radius=10)
        darkened = self.registry.execute("adjust_brightness", result, {"value": -burn})
        result = dark_mask.apply(result, darkened)

        # 微加对比度
        result = self.registry.execute("adjust_contrast", result, {"value": 10})
        return result

    # ---- 色彩氛围 ----

    def _exec_golden_hour(self, image: np.ndarray, p: dict) -> np.ndarray:
        intensity = p.get("intensity", 60)

        # 加暖色（降低蓝色通道 = 增加黄/橙）
        result = image.astype(np.float32)
        blue_reduce = intensity * 0.8 / 100.0
        result[:, :, 0] *= (1 - blue_reduce)  # B 通道降低

        # 增加红/橙
        red_boost = 1 + intensity * 0.4 / 100.0
        result[:, :, 2] = np.clip(result[:, :, 2] * red_boost, 0, 255)

        result = np.clip(result, 0, 255).astype(np.uint8)
        result = self.registry.execute("adjust_saturation", result, {"value": intensity // 5})
        result = self.registry.execute("adjust_contrast", result, {"value": intensity // 5})
        return result

    def _exec_moody_cool(self, image: np.ndarray, p: dict) -> np.ndarray:
        intensity = p.get("intensity", 50)

        # 加冷色（降低红色通道 = 增加青/蓝）
        result = image.astype(np.float32)
        red_reduce = intensity * 0.6 / 100.0
        result[:, :, 2] *= (1 - red_reduce)

        result = np.clip(result, 0, 255).astype(np.uint8)
        result = self.registry.execute("adjust_saturation", result, {"value": -intensity // 5})
        result = self.registry.execute("adjust_contrast", result, {"value": 10})
        return result

    def _exec_vibrant_pop(self, image: np.ndarray, p: dict) -> np.ndarray:
        intensity = p.get("intensity", 30)
        result = self.registry.execute("adjust_saturation", image, {"value": intensity})
        result = self.registry.execute("adjust_contrast", result, {"value": intensity // 3})
        return result

    # ---- 肖像 ----

    def _exec_skin_smooth(self, image: np.ndarray, p: dict) -> np.ndarray:
        strength = p.get("strength", 8)

        # 选区：肤色范围（简化版）
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        # 肤色 HSV 范围
        skin_mask = cv2.inRange(hsv, (0, 20, 70), (25, 170, 255))
        skin_mask = skin_mask.astype(np.float32) / 255.0
        skin_mask = cv2.GaussianBlur(skin_mask, (21, 21), 10)

        # 对肤色区域做双边滤波（保边平滑）
        smoothed = cv2.bilateralFilter(image, strength * 2 + 1, 75, 75)

        mask_3ch = np.stack([skin_mask] * 3, axis=-1)
        result = (image.astype(np.float32) * (1 - mask_3ch) +
                  smoothed.astype(np.float32) * mask_3ch).astype(np.uint8)
        return result

    def _exec_eye_enhance(self, image: np.ndarray, p: dict) -> np.ndarray:
        strength = p.get("strength", 15)

        # 简化：对画面中上部区域做锐化 + 提亮（假设眼睛在画面上方 1/3 处）
        h, w = image.shape[:2]
        eye_region = Mask.from_rectangle(image.shape, w//4, 0, w//2, h//3)
        eye_region.feather(radius=30)

        sharpened = self.registry.execute("apply_sharpen", image, {"strength": strength * 2})
        brightened = self.registry.execute("adjust_brightness", sharpened, {"value": strength})
        return eye_region.apply(image, brightened)

    # ---- 效果 ----

    def _exec_add_vignette(self, image: np.ndarray, p: dict) -> np.ndarray:
        intensity = p.get("intensity", 40)

        # 径向渐变蒙版（中心亮，边缘暗）
        vignette = Mask.from_gradient(image.shape, direction="center_to_edge")
        # 反转：越靠近边缘越暗
        vignette.invert()

        # 调低暗部强度
        strength = intensity * 1.5 / 100.0
        vignette.data = vignette.data * strength

        darkened = self.registry.execute("adjust_brightness", image, {"value": -intensity})
        return vignette.apply(image, darkened)

    def _exec_clarity_boost(self, image: np.ndarray, p: dict) -> np.ndarray:
        strength = p.get("strength", 30)

        # 清晰度 = 锐化 + 对比度（中调区域）
        result = self.registry.execute("apply_sharpen", image, {"strength": strength // 2})

        # 只对中间调增强对比度（不对高光和暗部）
        mid_mask = Mask.from_brightness_range(result, min_val=60, max_val=200)
        mid_mask.feather(radius=5)

        contrasted = self.registry.execute("adjust_contrast", result, {"value": strength // 3})
        result = mid_mask.apply(result, contrasted)

        return result


def get_all_skill_schemas() -> List[Dict]:
    """获取所有 Skill 的 LLM Function Schema。"""
    schemas = []
    for name, skill in SKILL_LIBRARY.items():
        props = {}
        required = []
        for param in skill.parameters:
            props[param["name"]] = {
                "type": param["type"],
                "description": f"{param['description']} (范围 {param['range'][0]}-{param['range'][1]}，默认 {param['default']})"
            }
            if param.get("required", False):
                required.append(param["name"])

        schemas.append({
            "name": name,
            "description": f"{skill.description}。适用场景: {skill.when_to_use}。示例: {skill.example}",
            "input_schema": {
                "type": "object",
                "properties": props,
                "required": required,
            }
        })
    return schemas


def get_skills_summary() -> str:
    """生成 Skills 摘要文本（用于 System Prompt）。"""
    lines = ["## 🎯 高级 Skills（组合操作）\n"]
    for name, skill in SKILL_LIBRARY.items():
        params_str = ", ".join(
            f"{p['name']}(默认{p['default']})" for p in skill.parameters
        )
        lines.append(f"- **{name}**: {skill.description}")
        lines.append(f"  参数: {params_str}")
        lines.append(f"  何时用: {skill.when_to_use}")
        lines.append("")
    return "\n".join(lines)
