# article-generator — 批量文章自动生成 Skill

## 触发条件

当用户提出以下需求时，应使用本 Skill：
- "批量生成文章"
- "根据主题生成文章"
- "生成公众号文章"
- "生成带图片占位符的文章"
- "输出 Excel 文章结果"
- 任何涉及"多个主题 + 自动写文章 + 输出 Excel"的请求

## Skill 概述

本 Skill 用于批量处理文章生成需求，支持：
1. 自然语言输入多个测例，自动解析主题、字数、图片数等参数
2. 智能判断是否需要检索外部材料
3. 自动生成大纲 → 标题 → 正文 → 转发文案 → 替补标题
4. 正文自动插入指定数量的图片占位符（格式：`AI配图中...`）
5. 自动自检：字数、占位符格式、标题质量等
6. 输出为规范的四列 Excel 文件

## 核心脚本

| 脚本 | 功能 |
|------|------|
| `scripts/article_generator.py` | 主 CLI 入口，编排完整流程 |
| `scripts/input_parser.py` | 自然语言 / Excel 输入解析 |
| `scripts/material_retriever.py` | 检索判断 + 材料获取 |
| `scripts/article_checker.py` | 文章质量自检 |
| `scripts/excel_writer.py` | Excel 输出 |

## 使用方式

### 方式 A：命令行直接输入

```bash
python3 scripts/article_generator.py \
  --input "以AI办公提效为主题，写一篇1200字文章，添加3个图片占位符；以企业知识库为主题，写一篇1000字文章，添加2个图片占位符"
```

### 方式 B：从 Excel 文件读取

```bash
python3 scripts/article_generator.py --input-file article_inputs/cases.xlsx
```

### 方式 C：运行内置示例测例

```bash
python3 scripts/article_generator.py --demo
```

## 默认参数

| 参数 | 默认值 |
|------|--------|
| 字数 | 1000 字 |
| 图片数量 | 0 张 |
| 写作风格 | 通俗、有传播力、适合公众号或知识类平台发布 |

## 图片占位符格式（严格）

使用标准 Markdown 图片语法：

```
![AI配图中...](图片0路径)
![AI配图中...](图片1路径)
![AI配图中...](图片2路径)
```

- 格式严格为 `![AI配图中...](图片n路径)`，n 从 0 开始连续递增
- alt 文本必须是 `AI配图中...`，路径必须是 `图片n路径`
- 不能写成"图片一""图片 1""image1"或其他格式
- 要分散插入正文合适位置，不能全部堆在开头或结尾

## Excel 输出

输出文件：`article_outputs/generated_articles.xlsx`

四列（严格）：
- 主题
- 文章正文（含 Markdown 标题 `# {主标题}`）
- 标题（含主标题 + 3 个替补标题）
- 转发文案（仅 2-3 句转发文案，不含替补标题）

## 详细工作流

见 `article_workflow.md`

## 质量检查清单

见 `quality_checklist.md`
