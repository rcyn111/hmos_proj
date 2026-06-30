# 使用指南 — HarmonyOS Dev Claw

> 面向 HarmonyOS 开发新手的完整使用指南。

---

## 第一步：环境准备

### 1.1 安装 Claude Code

按照 [Anthropic 官方文档](https://docs.anthropic.com/en/docs/claude-code) 安装 Claude Code CLI。

安装完成后，在终端中验证：

```bash
claude --version
```

如果显示版本号，说明安装成功。

### 1.2 获取 DeepSeek API Key

1. 访问 [DeepSeek 开放平台](https://platform.deepseek.com/)
2. 注册/登录
3. 在 "API Keys" 页面创建一个新的 API key
4. 复制保存（仅显示一次）

### 1.3 配置环境变量

在终端中执行（每次新终端窗口都需要执行）：

```bash
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="你的-deepseek-api-key"
export ANTHROPIC_MODEL="deepseek-v4-pro"
export ANTHROPIC_DEFAULT_OPUS_MODEL="deepseek-v4-pro"
export ANTHROPIC_DEFAULT_SONNET_MODEL="deepseek-v4-pro"
```

**推荐**：将以上内容添加到 `~/.zshrc`（如果使用 zsh）或 `~/.bashrc`（如果使用 bash），这样每次打开终端都会自动生效。

```bash
# 添加到 ~/.zshrc
echo 'export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"' >> ~/.zshrc
echo 'export ANTHROPIC_AUTH_TOKEN="你的-deepseek-api-key"' >> ~/.zshrc
echo 'export ANTHROPIC_MODEL="deepseek-v4-pro"' >> ~/.zshrc
echo 'export ANTHROPIC_DEFAULT_OPUS_MODEL="deepseek-v4-pro"' >> ~/.zshrc
echo 'export ANTHROPIC_DEFAULT_SONNET_MODEL="deepseek-v4-pro"' >> ~/.zshrc
source ~/.zshrc
```

### 1.4 安装 DevEco Studio（可选，运行时需要）

如果还没安装 DevEco Studio，参考 `knowledge/deveco/install.md`（Claw 可以帮你查安装步骤）。

---

## 第二步：启动 Claw

在项目目录中启动 Claude Code：

```bash
cd $PROJECT_ROOT
claude
```

启动后，你就进入了与 Claw 的对话界面。CLAUDE.md 中的规则会自动生效。

---

## 第三步：开始使用

### 场景 A：从零开始做一个 App

**第 1 步**：描述你的想法

```
我想做一个鸿蒙记事本 App，可以写笔记、查看笔记列表、删除笔记。
```

**第 2 步**：Claw 会调用 `harmony-requirement-analyzer`，输出：
- 对你需求的理解确认
- 功能列表
- 页面结构
- 开发分阶段计划
- 当前第一步要做什么

**第 3 步**：确认后，Claw 逐步帮你生成代码。

### 场景 B：添加一个新页面

```
帮我在现有项目中添加一个"关于"页面，显示 App 名称、版本号和作者。
```

Claw 会调用 `harmony-arkui-page-builder`，先说明要修改的文件，再生成代码。

### 场景 C：报错了

把完整的报错信息贴过来：

```
DevEco Studio 编译报错：
ArkTS:ERROR File: /Users/.../entry/src/main/ets/pages/Index.ets:15:20
'Text' is not a valid component
```

Claw 会调用 `harmony-error-fixer`，用中文解释报错含义并给出修复方案。

### 场景 D：检查代码质量

```
帮我检查一下 pages/ 目录下的所有代码。
```

Claw 会调用 `harmony-code-reviewer`，逐文件审查并输出报告。

### 场景 E：查 API 用法

```
ArkUI 的 Column 和 Row 组件有什么区别？怎么用？
```

Claw 会调用 `harmony-doc-searcher` 搜索官方文档并整理答案。

---

## 第四步：理解输出

### Claw 每次改代码前都会说清楚

在每次修改代码前，Claw 会先输出类似这样的说明：

```
📋 修改计划：
- 文件：projs/MyApp/entry/src/main/ets/pages/Index.ets
- 操作：在 build() 方法中添加一个 Button 组件
- 原因：需要添加"添加笔记"的入口按钮
- 风险：低，只在现有页面增加一个组件
是否继续？
```

你确认后 Claw 才会修改。

### 每次做完都会生成复盘记录

在 `runs/` 目录下，每次 skill 执行后都会生成一个 Markdown 文件，包含：
- 做了什么
- 成功点和错误点
- 评分（0-5 分）
- 改进建议

你可以随时查看这些记录。

---

## 第五步：查看和利用知识库

### 知识库在哪里

`knowledge/` 目录下有关于 HarmonyOS 开发的整理好的知识。

### 知识库什么时候更新

每次 Claw 帮你解决了问题或学到了新东西后，都会自动判断是否需要更新知识库。

### 你自己也可以手动查看

```bash
# 查看 ArkUI 组件知识
cat knowledge/harmonyos/arkui.md

# 查看常见错误和解决方案
cat knowledge/harmonyos/common_errors.md
```

---

## 常见问题

### Q: Claw 会自动删我的代码吗？

A: 不会。删除任何文件前 Claw 都会先问你确认。

### Q: Claw 生成的代码能直接在 DevEco Studio 中运行吗？

A: 目标是能。如果不行，把报错贴给 Claw，它会帮你修复。

### Q: 如何使用 Claw 管理多个 HarmonyOS 项目？

A: 把你的不同项目放在 `projs/` 下的不同子目录中，Claw 可以访问它们。

### Q: 怎么让 Claw 只改某个项目，不改另一个？

A: 在对话中指定项目路径即可，比如"只修改 projs/MyApp1/ 下的文件"。

---

## 命令速查

| 我想做什么 | 我该说什么 |
|-----------|-----------|
| 创建新 App | "我想做一个 xxx App，功能有 a、b、c" |
| 添加页面 | "帮我添加一个 xxx 页面" |
| 修改页面 | "帮我修改 xxx 页面，改为 yyy" |
| 修复报错 | "运行时报错：xxx（贴完整报错）" |
| 搜索 API | "xxx API 怎么用？" |
| 审查代码 | "帮我审查 xxx 文件的代码" |
| 查知识库 | "knowledge/ 里有没有关于 xxx 的资料？" |
| 看历史 | "runs/ 里最近几次执行有什么问题？" |

---

> 记住：你只需要用自然语言描述你想做什么，Claw 会帮你完成剩下的。
