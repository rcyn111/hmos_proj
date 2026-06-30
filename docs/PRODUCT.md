# 产品定义 — HarmonyOS Dev Claw

## 一句话定义

HarmonyOS Dev Claw 是一个面向鸿蒙应用开发新手的本地 AI Agent 工作台，基于 Claude Code + DSAPI，支持需求拆解、资料检索、知识库沉淀、Skill 自动配置、项目文件读写、执行复盘和 Skill 自优化。

---

## 产品定位

### 不是什么
- ❌ 不是 HarmonyOS 应用商店
- ❌ 不是在线 IDE
- ❌ 不是后端服务
- ❌ 不是 App 发布工具
- ❌ 不是多 Agent 调度平台
- ❌ 不是零代码/低代码平台

### 是什么
- ✅ 本地命令行 AI 开发助手
- ✅ HarmonyOS 开发知识库
- ✅ 可自定义的 Skill 工作流引擎
- ✅ 执行记录和复盘系统
- ✅ Skill 自我优化系统

---

## 目标用户

**主用户群**：HarmonyOS / 鸿蒙 OS 开发完全新手

用户特征：
- 可能不了解 ArkTS、ArkUI、DevEco Studio
- 有编程基础（但不一定是 TypeScript 或移动开发）
- 希望通过自然语言描述来开发鸿蒙应用
- 需要步骤清晰、解释充分的引导

---

## 核心价值

| 痛点 | Claw 的解决方案 |
|------|----------------|
| HarmonyOS 官方文档太多，不知道从哪看起 | `harmony-doc-searcher` 按需精准搜索 |
| API 太多记不住，经常写错 | 不确定就搜索，绝不编造 |
| 报错信息看不懂 | `harmony-error-fixer` 用中文解释并修复 |
| 不知道怎么拆功能 | `harmony-requirement-analyzer` 自动拆成小步骤 |
| 做完就忘，下次遇到同样问题还要重新查 | `knowledge/` 知识库积累，越用越省事 |
| AI 经常编造 API | 强制执行搜索 + 不确定就标记 |
| AI 生成的代码质量参差不齐 | `harmony-code-reviewer` 自动审查 |
| Skill（工作流程）越用越不好用 | `harmony-skill-evolver` 根据执行结果自动优化 |

---

## 核心工作流

```
用户输入自然语言需求
    │
    ▼
① 理解需求 — 复述并确认
    │
    ▼
② 检查知识库 — 查看 knowledge/ 是否有相关经验
    │
    ▼
③ 搜索资料（如需）— 查阅官方文档
    │
    ▼
④ 选择 Skill — 匹配最合适的 skill
    │
    ▼
⑤ 执行 Skill — 按步骤生成/修改代码
    │
    ▼
⑥ 记录复盘 — 生成 runs/ 复盘报告
    │
    ▼
⑦ 更新知识库 — 新知识写入 knowledge/
    │
    ▼
⑧ Skill 自进化 — 判断是否优化 skill
    │
    └──── 闭环：下次更准 ────┘
```

---

## 版本规划

| 版本 | 范围 | 状态 |
|------|------|------|
| v0.1.0 | 最小可运行版本：基础目录结构、6 个 skill、知识库模板、复盘模板 | 当前 |
| v0.2.0 | 接入 web 搜索，完善知识库内容 | 计划中 |
| v0.3.0 | 第一个完整开发案例（待办 App）端到端验证 | 计划中 |
| v1.0.0 | 可稳定用于日常开发的版本 | 计划中 |

---

## 技术架构

详见 `docs/ARCHITECTURE.md`。

## 使用指南

详见 `docs/USAGE.md`。

## 路线图

详见 `docs/ROADMAP.md`。
