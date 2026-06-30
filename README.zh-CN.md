# HarmonyOS Dev Claw

> 面向鸿蒙（HarmonyOS）应用开发新手的本地 AI Agent 工作台。

[English](README.md) | [中文](README.zh-CN.md)

## 这是什么？

HarmonyOS Dev Claw 是一个跑在你本机上的 AI 开发助手。你只需要用自然语言描述你想做的鸿蒙 App 功能，它就会帮你：

1. **拆解需求** — 把模糊的想法变成清晰的开发计划
2. **搜索资料** — 自动查找 HarmonyOS 官方文档和社区教程
3. **生成代码** — 帮你写 ArkTS + ArkUI 页面代码
4. **修复报错** — 帮你分析编译或运行时的错误
5. **审查代码** — 检查你的代码质量
6. **持续进化** — 每次用完自动总结，下次更聪明

## 你需要准备什么？

### 1. 安装 Claude Code

按照 [Anthropic 官方文档](https://docs.anthropic.com/en/docs/claude-code) 安装 Claude Code CLI。

### 2. 配置 DSAPI（DeepSeek API）

Claw 使用 DeepSeek 作为模型服务。在终端中设置以下环境变量：

```bash
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="你的-deepseek-api-key"
export ANTHROPIC_MODEL="deepseek-v4-pro"
export ANTHROPIC_DEFAULT_OPUS_MODEL="deepseek-v4-pro"
export ANTHROPIC_DEFAULT_SONNET_MODEL="deepseek-v4-pro"
```

> ⚠️ **重要**：API key 只应设置在终端环境变量中，**不要写进项目的任何文件里**。

详细的配置说明见 `config/dsapi.env.example`。

### 3. 启动 Claude Code

在项目目录中启动：

```bash
cd $PROJECT_ROOT
claude
```

进入 Claude Code 后，你就可以用自然语言开始开发了。

## 怎么使用？

### 场景 1：我想做一个新 App

直接说：

> "我想做一个鸿蒙待办事项 App，支持添加、删除、标记完成"

Claw 会自动调用 `harmony-requirement-analyzer` 帮你分析需求，输出开发计划。

### 场景 2：帮我写一个页面

> "帮我写一个登录页面，有用户名输入框、密码输入框和登录按钮"

Claw 会调用 `harmony-arkui-page-builder` 生成 ArkUI 代码。

### 场景 3：代码报错了

直接把报错信息贴过来：

> "DevEco Studio 报错：ArkTS:ERROR ..."

Claw 会调用 `harmony-error-fixer` 分析并给出修复方案。

### 场景 4：帮我查一个 API

> "ArkUI 的 List 组件怎么用？"

Claw 会调用 `harmony-doc-searcher` 搜索官方文档。

### 场景 5：检查我的代码

> "帮我审查一下刚写的 Index.ets"

Claw 会调用 `harmony-code-reviewer` 检查代码质量。

## 项目结构

```
hmos_proj/
├── CLAUDE.md              # Claude Code 工作规则（最高优先级）
├── README.md              # 本文件
├── config/                # 配置文件
│   ├── dsapi.env.example  # DSAPI 配置示例
│   ├── permissions.md     # 权限规则
│   └── claw_config.yaml   # Claw 行为配置
├── docs/                  # 产品文档
│   ├── PRODUCT.md         # 产品定义
│   ├── ROADMAP.md         # 路线图
│   ├── ARCHITECTURE.md    # 架构说明
│   └── USAGE.md           # 使用指南
├── knowledge/             # 本地知识库（越用越丰富）
│   ├── harmonyos/         # ArkTS / ArkUI / 路由 / 存储 / 权限
│   ├── deveco/            # DevEco Studio 相关
│   └── project/           # 项目决策和经验
├── .claude/skills/        # Skill 定义（6 个核心技能）
├── prompts/               # 提示词模板
├── runs/                  # 每次执行的复盘记录
├── memory/                # 用户偏好、进化日志、任务记录
├── scripts/               # 辅助脚本
└── projs/                 # 你的 HarmonyOS 项目放这里
```

## 核心 Skill 列表

| Skill | 做什么 | 什么时候用 |
|-------|--------|-----------|
| `harmony-requirement-analyzer` | 需求分析 + 开发计划 | 想做新功能时 |
| `harmony-doc-searcher` | 搜索官方文档 | 不确定 API 写法时 |
| `harmony-arkui-page-builder` | 生成页面代码 | 需要写界面时 |
| `harmony-error-fixer` | 分析和修复报错 | 编译/运行出错时 |
| `harmony-code-reviewer` | 检查代码质量 | 写完功能后 |
| `harmony-skill-evolver` | 自动优化 skill | 每次执行结束后 |

## 工作流程

Claw 每次都会按以下流程工作：

```
理解需求 → 查知识库 → 搜索资料 → 执行 skill → 记录复盘 → 更新知识库 → 优化 skill
```

每次执行后都会在 `runs/` 目录留下完整的复盘记录，你可以随时查看。

## 新手须知

如果你是 HarmonyOS 开发新手，不用担心。Claw 会：

- 用**中文**和你交流
- 每个操作前**先解释**要做什么、为什么
- 每次只做**一个小功能**，不乱改
- 涉及的专业概念**第一次出现时都会解释**
- 不确定的 API **宁可说不知道也不会编造**

### 你可能需要了解的术语

| 术语 | 简单解释 |
|------|---------|
| HarmonyOS | 华为开发的操作系统，手机上跑的那个 |
| ArkTS | HarmonyOS 官方推荐的编程语言，和 TypeScript 很像 |
| ArkUI | HarmonyOS 的界面框架，用声明式语法写界面 |
| DevEco Studio | HarmonyOS 的官方开发工具（IDE），类似 VS Code |
| HAP | HarmonyOS 应用的安装包格式，类似 Android 的 APK |
| @Component | ArkUI 中声明一个自定义组件的装饰器 |
| @State | ArkUI 中声明一个状态变量，变了界面就自动刷新 |

## 常见问题

### Q: Claw 能自动发布应用吗？

A: 不能。第一版只帮你开发，不帮你发布。

### Q: Claw 会自动修改我的代码吗？

A: 每次修改前都会先告诉你改哪个文件、为什么改，等你确认后才动手。

### Q: 我的代码会被上传到云端吗？

A: 你的项目文件只在你本地。API 调用会经过你配置的 DeepSeek 服务。

### Q: API key 放哪里安全？

A: 只放在你本机的终端环境变量中（如 `~/.zshrc`），项目里只有 `.example` 示例文件。

---

> 开始使用：启动 Claude Code，然后说"我想做一个 xxx App"即可。
