# 文章批量生成器 — 使用说明

> 批量处理文章生成需求，自动解析参数、生成正文（含图片占位符）、自检、输出 Excel。

## 1. 安装依赖

```bash
cd $PROJECT_ROOT
pip install -r requirements.txt
```

核心依赖：
- `anthropic`：调用 LLM API 生成文章
- `pandas` + `openpyxl`：Excel 读写
- `python-dotenv`：环境变量管理

## 2. 配置 API

本工具通过 Anthropic SDK 调用 DSAPI（DeepSeek API）。

在终端中设置环境变量：

```bash
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="你的-deepseek-api-key"
export ANTHROPIC_MODEL="deepseek-v4-pro"
```

> ⚠️ 如果未设置 `ANTHROPIC_AUTH_TOKEN`，工具将自动降级为**模拟生成模式**，
> 生成占位文章以验证整个流程是否跑通。

## 3. 使用方式

### 方式 A：命令行直接输入

多个测例用中文分号 `；` 分隔：

```bash
python3 scripts/article_generator.py \
  --input "以AI办公提效为主题，写一篇1200字文章，添加3个图片占位符；以企业知识库为主题，写一篇1000字文章，添加2个图片占位符"
```

### 方式 B：从 Excel / CSV 文件读取

**结构化列模式**（推荐）— Excel 包含以下列：

| 主题 | 字数 | 图片数量 | 其他要求 |
|------|------|----------|----------|
| AI办公提效 | 1200 | 3 | 偏营销风格 |
| 企业知识库建设 | 1000 | 2 | |

```bash
python3 scripts/article_generator.py --input-file article_inputs/cases.xlsx
```

**单列模式**— Excel 只有一列"需求"，每行是一个自然语言测例：

| 需求 |
|------|
| 以AI办公提效为主题，写一篇1200字文章，添加3个图片占位符 |
| 以企业知识库为主题，写一篇1000字文章，添加2个图片占位符 |

```bash
python3 scripts/article_generator.py --input-file article_inputs/cases.csv
```

### 方式 C：运行内置 demo

```bash
python3 scripts/article_generator.py --demo
```

这会运行 3 个内置示例测例。

### 自定义输出路径

```bash
python3 scripts/article_generator.py --demo --output article_outputs/my_result.xlsx
```

## 4. 输出文件

**默认路径**：`article_outputs/generated_articles.xlsx`

**四列（严格）**：

| 列名 | 说明 |
|------|------|
| 主题 | 文章主题 |
| 文章正文 | Markdown 格式正文（顶部带 `# {标题}`），含图片占位符 |
| 标题 | 主标题 + 3 个替补标题 |
| 转发文案 | 2-3 句转发文案（不含替补标题） |

## 5. 图片占位符格式规则

使用标准 Markdown 图片语法（每行一个）：

```
![AI配图中...](图片0路径)
![AI配图中...](图片1路径)
![AI配图中...](图片2路径)
```

**规则**：
- 格式严格为 `![AI配图中...](图片n路径)`，n 从 0 开始连续递增
- alt 文本必须是 `AI配图中...`，路径必须是 `图片n路径`
- 不能写成"图片一""图片 1""image1"或其他格式
- 占位符要分散在正文合适位置，不能全部堆在开头或结尾
- 如果图片数量为 0，正文中不出现任何占位符

## 6. 默认参数

| 参数 | 默认值 |
|------|--------|
| 字数 | 1000 字 |
| 图片数量 | 0 |
| 写作风格 | 通俗、有传播力、适合公众号或知识类平台发布 |
| 目标受众 | 通用 |
| 发布平台 | 公众号 |

## 7. 工作流程

```
输入解析 → 检索判断 → 大纲生成 → 标题生成 → 正文生成 → 自检修复 → 转发文案 → 替补标题 → 写入 Excel
```

每次生成后自动执行自检（字数、图片格式、标题质量等），不通过则自动修复（最多 2 次）。

## 8. 文件结构

```
skills/article-generator/
├── SKILL.md              # Skill 定义
├── article_workflow.md   # 详细工作流
├── quality_checklist.md  # 质量检查清单
└── README.md             # 本文件

scripts/
├── article_generator.py  # 主 CLI 脚本
├── input_parser.py       # 输入解析
├── material_retriever.py # 材料检索
├── article_checker.py    # 文章自检
└── excel_writer.py       # Excel 输出

article_inputs/            # 输入文件存放
article_outputs/           # 输出文件存放
```

## 9. 模拟模式说明

当未配置 API key 或无法连接 API 时，工具自动进入**模拟生成模式**：
- 生成结构完整的占位文章
- 格式、图片占位符、字数等均符合规范
- 可验证整个流程（解析 → 生成 → 检查 → Excel 输出）是否跑通
- 在日志中会标注"使用模拟模式生成内容"

要获得真正的 AI 生成文章，请确保已正确配置 `ANTHROPIC_AUTH_TOKEN` 环境变量。
