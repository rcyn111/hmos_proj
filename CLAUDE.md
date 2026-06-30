# CLAUDE.md — HarmonyOS Dev Claw

> **本文件是 Claude Code 在本项目中的最高优先级工作规则。**
> 任何与本文件冲突的默认行为，一律以本文件为准。

---

## 1. 项目身份

**HarmonyOS Dev Claw** 是一个面向鸿蒙（HarmonyOS）应用开发新手的本地 Agent 工作台。

**一句话定义**：HarmonyOS Dev Claw 是一个面向鸿蒙应用开发新手的本地 Agent 工作台，基于 Claude Code + DSAPI，支持需求拆解、资料检索、知识库沉淀、Skill 自动配置、项目文件读写、执行复盘和 Skill 自优化。

**核心闭环**：

```
用户需求 → 拆解 → 搜索资料 → 执行 skill → 记录复盘 → 更新知识库 → 优化 skill
    ↑                                                                    │
    └──────────────── 下次执行更准 ←─────────────────────────────────────┘
```

**项目根目录结构**：

```
hmos_proj/
├── CLAUDE.md              # 本文件 — 最高优先级工作规则
├── README.md              # 项目使用说明（面向新手）
├── config/                # 配置文件
│   ├── dsapi.env.example  # DSAPI 配置示例（不含真实 key）
│   ├── permissions.md     # 权限规则详细说明
│   └── claw_config.yaml   # Claw 行为配置
├── docs/                  # 产品文档
│   ├── PRODUCT.md         # 产品定义
│   ├── ROADMAP.md         # 路线图
│   ├── ARCHITECTURE.md    # 架构说明
│   └── USAGE.md           # 使用指南
├── knowledge/             # 本地知识库
│   ├── harmonyos/         # ArkTS / ArkUI / 路由 / 存储 / 权限 / 错误
│   ├── deveco/            # DevEco Studio 安装 / 调试 / 错误
│   └── project/           # 需求 / 架构 / 决策 / 经验教训
├── .claude/
│   └── skills/            # Skill 定义目录
│       ├── harmony-requirement-analyzer/SKILL.md
│       ├── harmony-doc-searcher/SKILL.md
│       ├── harmony-arkui-page-builder/SKILL.md
│       ├── harmony-error-fixer/SKILL.md
│       ├── harmony-code-reviewer/SKILL.md
│       └── harmony-skill-evolver/SKILL.md
├── prompts/               # 提示词模板
├── runs/                  # Skill 执行复盘记录
├── memory/                # 用户偏好 / Skill 进化日志 / 决策记录 / 任务看板
├── scripts/               # 辅助脚本
└── projs/                 # 用户 HarmonyOS 项目存放目录
```

---

## 2. 用户画像

- **目标用户：HarmonyOS 开发新手**。
- 用户可能不了解以下概念（首次出现时必须简要解释）：
  - ArkTS（HarmonyOS 官方推荐的开发语言，基于 TypeScript 扩展）
  - ArkUI（HarmonyOS 的声明式 UI 框架）
  - DevEco Studio（HarmonyOS 官方 IDE）
  - HAP（HarmonyOS 应用安装包）
  - Ability（应用的基本组成单元）
  - Stage 模型（HarmonyOS 应用架构模型）
- 用户需要**步骤清晰、解释充分**的指导。
- **不要一次性进行大范围改动**，每次只做一件事，做完确认后再继续下一步。
- 用户使用 **DSAPI / DeepSeek** 作为模型服务的 Anthropic 兼容接口。

---

## 3. 技术目标

使用 Claude Code + DSAPI 构建一个可以辅助 HarmonyOS 应用开发的 Claw 工作台。

| 能力 | 说明 |
|------|------|
| 需求拆解 | 将用户模糊的需求拆解为可执行的小步骤 |
| 资料搜索 | 搜索 HarmonyOS 官方文档、社区博客、示例代码 |
| 知识库沉淀 | 将每次执行中获取的知识写入 `knowledge/` 目录 |
| Skill 调用 | 通过 `.claude/skills/` 中的 skill 完成特定任务 |
| Skill 执行复盘 | 每次 skill 执行后在 `runs/` 目录记录完整复盘报告 |
| Skill 自进化 | 通过 `harmony-skill-evolver` 根据复盘结果自动优化 skill |

### 已有 6 个 Skill

| Skill | 用途 | 文件 |
|-------|------|------|
| harmony-requirement-analyzer | 需求分析 → PRD + 功能拆解 + 开发计划 | `.claude/skills/harmony-requirement-analyzer/SKILL.md` |
| harmony-doc-searcher | 搜索 HarmonyOS 官方文档和社区资料 | `.claude/skills/harmony-doc-searcher/SKILL.md` |
| harmony-arkui-page-builder | 生成 ArkTS + ArkUI 页面代码 | `.claude/skills/harmony-arkui-page-builder/SKILL.md` |
| harmony-error-fixer | 分析并修复编译/运行报错 | `.claude/skills/harmony-error-fixer/SKILL.md` |
| harmony-code-reviewer | 审查鸿蒙项目代码质量 | `.claude/skills/harmony-code-reviewer/SKILL.md` |
| harmony-skill-evolver | 根据执行复盘优化已有 skill | `.claude/skills/harmony-skill-evolver/SKILL.md` |
| harmony-ime-skin-builder | 创建自定义输入法皮肤项目 | `.claude/skills/harmony-ime-skin-builder/SKILL.md` |

---

## 4. 权限范围

### 4.1 允许的操作（白名单）

- 读取和写入当前项目目录（`$PROJECT_ROOT/`）及其所有子目录。
- 创建子目录。
- 修改以下目录中的文件：
  - `.claude/skills/` — skill 定义
  - `config/` — 配置文件（除 `.env` 需确认）
  - `docs/` — 产品文档
  - `knowledge/` — 知识库
  - `runs/` — 执行记录
  - `memory/` — 记忆文件
  - `scripts/` — 脚本
  - `prompts/` — 提示词模板
  - `projs/` — 用户 HarmonyOS 项目
- 使用 `WebSearch` 和 `WebFetch` 搜索 HarmonyOS 官方文档和社区资料。

### 4.2 禁止的操作（黑名单）

- **禁止访问**当前项目目录（`$PROJECT_ROOT/`）之外的任何文件。
- **禁止读取或修改**用户主目录下与本项目无关的文件。
- **禁止泄露、记录、打印** API key、token、密钥等敏感信息。
- **禁止将真实密钥写入**日志、知识库、运行记录、Git 仓库或任何项目文件。

### 4.3 需先请求用户确认的操作（灰名单）

以下操作**必须**先向用户说明并获得确认后才能执行：

- 删除文件（包括 `rm`、覆盖式写入已有文件）
- 大范围重构（涉及 3 个以上文件的变更）
- 覆盖重要配置文件（`CLAUDE.md`、`settings.json`、skill 定义文件、`claw_config.yaml`）
- 执行高风险 shell 命令（`rm -rf`、`git reset --hard`、`git clean`）
- 修改 `.env` 文件
- 安装全局依赖
- 访问项目目录外的任何路径

### 4.4 DSAPI 密钥防泄露措施

- 真实 API key **仅应存在于**用户终端环境变量或本机 shell 配置文件中（如 `~/.zshrc`）。
- 项目内仅存在 `config/dsapi.env.example`（示例文件），不含真实 key。
- `.gitignore` 必须忽略 `*.env` 和 `.env` 文件。
- CLAUDE.md 明确禁止在任何项目文件中写入密钥。
- 复盘模板（`runs/`）中不含密钥字段。
- 知识库（`knowledge/`）中不得写入密钥。

---

## 5. 工作流程

每次任务**必须**遵循以下全流程，不得跳过任何步骤：

```
理解需求 → 检查知识库 → 搜索资料（如需）→ 选择或创建 skill → 执行任务 → 记录执行结果 → 总结优缺点 → 更新知识库 → 判断是否优化 skill
```

### 各步骤详细说明

1. **理解需求**：用自己的话复述用户需求，确认理解正确后再继续。需求不清时必须主动提问澄清。
2. **检查知识库**：先查看 `knowledge/` 目录和 `runs/` 历史记录，是否有相关知识和经验。
3. **搜索资料**：遇到不确定的 HarmonyOS API、报错、最佳实践时，先用 `WebSearch` + `WebFetch` 查官方文档（`developer.huawei.com`）。
4. **选择或创建 skill**：检查 `.claude/skills/` 下是否已有匹配的 skill。有则使用，无则创建。
5. **执行任务**：按 skill 定义的步骤逐步执行，每完成一步向用户汇报并等待确认。
6. **记录执行结果**：在 `runs/` 目录生成完整复盘记录（格式见第 6 节）。
7. **总结优缺点**：分析本次执行做得好的地方和需要改进的地方。
8. **更新知识库**：将新发现的知识写入 `knowledge/` 对应目录，将报错和解决方案写入 `common_errors.md`。
9. **判断是否优化 skill**：通过 `harmony-skill-evolver` 判断是否需要优化 skill 定义。

---

## 6. Skill 执行复盘要求

每次 skill 执行完成后，**必须**在 `runs/` 目录下生成一份复盘记录文件。

### 文件命名格式

```
runs/YYYY-MM-DD_HH-mm-ss_{skill-name}.md
```

例如：`runs/2026-06-04_14-30-00_harmony-requirement-analyzer.md`

### 复盘记录必须包含的 16 个字段

```markdown
# 执行复盘：{skill-name}

- **执行时间**：{YYYY-MM-DD HH:mm:ss}
- **本次用户需求**：{用户原始需求的简要描述}
- **调用的 skill**：{skill 文件路径}

## 输入信息
- {输入的具体内容}

## 输出结果摘要
- {输出的主要内容总结}

## 修改文件清单
- {文件路径 1} — {修改说明}
- {文件路径 2} — {修改说明}

## 成功点
- {做得好的地方 1}
- {做得好的地方 2}

## 错误点
- {出错的地方 1}（如有，无则写"无"）
- {出错的地方 2}（如有）

## 未解决问题
- {本次未解决、需要后续处理的问题}（如有，无则写"无"）

## 是否完成目标
- [ ] 是 / [ ] 否
- 如未完成，原因：{说明}

## 评分（0-5 分）
- **任务完成度**：{0-5}
- **代码正确性**：{0-5}
- **解释清晰度**：{0-5}

## 是否需要人工返工
- [ ] 是 / [ ] 否
- 返工内容：{说明}

## 是否需要更新 knowledge/
- [ ] 是 / [ ] 否
- 更新内容：{简述更新的文件和内容}

## 是否需要优化对应 skill
- [ ] 是 / [ ] 否
- 优化内容：{简述优化了 SKILL.md 的什么内容}

## 下次改进建议
- {建议 1}
- {建议 2}
```

---

## 7. 新手友好要求

这是本项目**最高优先级的行为准则**。每次与用户交互都必须遵守：

1. **解释必须清楚**：每个操作前说明"我要做什么"和"为什么这样做"。
2. **代码修改必须说明文件路径**：每次 `Edit` 或 `Write` 操作前，先说明要修改哪个文件、为什么修改。
3. **每次只完成一个小功能**：不要在一次回复中同时修改多个不相关的功能。功能的粒度应控制在"一个页面 / 一个组件 / 一次报错修复"。
4. **不要默认引入复杂框架**：保持代码简洁，仅在确有必要时引入新依赖。优先使用 ArkUI 内置能力。
5. **首次出现必须解释**：HarmonyOS、ArkTS、ArkUI、DevEco Studio、HAP、Ability、Stage 模型、@Entry、@Component、@State 等概念在首次出现时必须用一两句话简要解释。
6. **不要假设用户知道路径**：涉及文件操作时，始终使用绝对路径。
7. **先确认再执行**：大改动前先列出计划，让用户确认。

---

## 8. HarmonyOS 开发要求

### 技术选型

- **优先使用 ArkTS 和 ArkUI** 编写应用代码。
  - ArkTS：HarmonyOS 官方推荐的开发语言，基于 TypeScript 扩展，增加了声明式 UI 装饰器。
  - ArkUI：HarmonyOS 的声明式 UI 框架，用 `@Component`、`@State`、`build()` 等构建界面。
- **优先参考官方文档**：
  - 主文档：`https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/`
  - API 参考：`https://developer.huawei.com/consumer/cn/doc/harmonyos-references/`

### API 使用原则

- 遇到不确定的 HarmonyOS API 时，**必须先搜索资料**或明确标记为"不确定"。
- **严禁编造 HarmonyOS API**。如果找不到官方文档，直接告知用户当前信息不足。
- 使用的每个 API 都应能在官方文档中找到对应说明。

### 项目结构参考

在 `projs/` 目录中创建 HarmonyOS 项目时，应遵循 DevEco Studio 生成的默认目录结构：
```
projs/{project-name}/
├── AppScope/
├── entry/
│   └── src/main/ets/pages/
├── build-profile.json5
├── hvigorfile.ts
└── oh-package.json5
```
如需自定义结构，必须先向用户说明原因。

### 搜索资料要求

- **优先级**：官方文档 > 高质量博客/社区 > 一般资料
- 每条搜索到的资料必须标注：
  - 来源链接
  - 搜索时间
  - 适用 HarmonyOS 版本
  - 可信度（高/中/低/待验证）
  - 是否已实际验证
- 搜索结果整理后存入 `knowledge/` 对应目录。

---

## 9. DSAPI 配置

本项目使用 DSAPI / DeepSeek 的 Anthropic 兼容接口作为模型服务。

### 配置方式

在终端中设置环境变量（**不要写入项目文件**）：

```bash
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="你的-deepseek-api-key"
export ANTHROPIC_MODEL="deepseek-v4-pro"
export ANTHROPIC_DEFAULT_OPUS_MODEL="deepseek-v4-pro"
export ANTHROPIC_DEFAULT_SONNET_MODEL="deepseek-v4-pro"
```

### 配置示例文件

项目中的 `config/dsapi.env.example` 仅包含示例，不含真实 key。真实 key 只应由用户在自己本机管理。

---

## 10. Skill 自进化规则

通过 `harmony-skill-evolver` 在每次执行后判断是否需要优化 skill。

### 规则

1. 先读取 `runs/` 中的最新复盘记录。
2. 分析其中的错误点和改进建议。
3. **排除外部因素**后再判断是否 skill 本身有问题：
   - ❌ 用户需求不清 → 不归咎于 skill
   - ❌ 环境缺失 / 依赖未安装 → 不归咎于 skill
   - ✅ 执行步骤顺序不当 → 可优化 skill
   - ✅ 输出格式不满足需求 → 可优化 skill
   - ✅ 缺少关键检查步骤 → 可优化 skill
4. **不能因一次偶然失败就盲目大改 skill**。
5. 优化后必须在 `memory/skill_evolution_log.md` 中记录变更原因和预期效果。

---

## 11. 项目规范

- **语言**：所有文档、注释、与用户交流均使用中文。
- **编码**：代码文件使用 UTF-8。
- **缩进**：ArkTS 代码使用 2 空格缩进。
- **命名**：ArkTS 文件使用 PascalCase（如 `Index.ets`），变量和函数使用 camelCase。
- **换行**：所有文本文件以 LF 结尾。

---

> **最后提醒**：本文件是所有工作规则的唯一权威来源。遇到本文件未覆盖的情况时，优先遵循"新手友好"和"先确认再执行"原则。
