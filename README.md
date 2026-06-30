# HarmonyOS Dev Claw

A local AI agent workbench for HarmonyOS (ArkTS/ArkUI) development beginners.

[English](README.md) | [中文](README.zh-CN.md)

## What is this?

HarmonyOS Dev Claw is an AI-powered development assistant that runs locally on your machine. Describe what HarmonyOS app feature you want in plain language, and it will:

1. **Analyze requirements** — turn vague ideas into clear development plans
2. **Search docs** — find relevant HarmonyOS official docs and community resources
3. **Generate code** — write ArkTS + ArkUI page code
4. **Fix errors** — analyze and fix compilation or runtime errors
5. **Review code** — check code quality
6. **Self-evolve** — learn from each execution to improve next time

## Prerequisites

### 1. Install Claude Code

Follow the [Anthropic docs](https://docs.anthropic.com/en/docs/claude-code) to install Claude Code CLI.

### 2. Configure DSAPI (DeepSeek API)

Set these environment variables in your terminal:

```bash
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="your-deepseek-api-key"
export ANTHROPIC_MODEL="deepseek-v4-pro"
export ANTHROPIC_DEFAULT_OPUS_MODEL="deepseek-v4-pro"
export ANTHROPIC_DEFAULT_SONNET_MODEL="deepseek-v4-pro"
```

> ⚠️ **Important**: Store your API key only in terminal environment variables — never write it into project files.

See `config/dsapi.env.example` for details.

### 3. Start Claude Code

```bash
cd $PROJECT_ROOT
claude
```

## Usage Examples

### Build a new app
> "I want to build a HarmonyOS todo app with add, delete, and mark-complete features."

### Write a page
> "Write a login page with username, password fields, and a login button."

### Fix an error
> "DevEco Studio error: ArkTS:ERROR ..."

Paste the error directly and Claw will analyze and suggest fixes.

### Look up an API
> "How do I use ArkUI's List component?"

### Review my code
> "Review the Index.ets I just wrote."

## Project Structure

```
hmos_proj/
├── CLAUDE.md              # Claude Code work rules (highest priority)
├── .claude/skills/        # 6 core skill definitions
├── config/                # Configuration files
├── docs/                  # Product docs
├── knowledge/             # Local knowledge base
│   ├── harmonyos/         # ArkTS / ArkUI / Router / Storage / Permissions
│   ├── deveco/            # DevEco Studio install / debug / errors
│   └── project/           # Decisions and lessons learned
├── prompts/               # Prompt templates
├── scripts/               # Helper scripts
└── projs/                 # Your HarmonyOS projects go here
```

## Core Skills

| Skill | Purpose |
|-------|---------|
| `harmony-requirement-analyzer` | Requirements analysis → PRD + dev plan |
| `harmony-doc-searcher` | Search HarmonyOS docs and community resources |
| `harmony-arkui-page-builder` | Generate ArkTS + ArkUI page code |
| `harmony-error-fixer` | Analyze and fix compilation/runtime errors |
| `harmony-code-reviewer` | Code quality review |
| `harmony-skill-evolver` | Auto-optimize skills from execution reviews |

## How It Works

```
Understand → Check Knowledge Base → Search Docs → Execute Skill → Record Review → Update KB → Optimize Skill
```

Each execution leaves a detailed review in `runs/` so you can always look back.

## Glossary

| Term | Description |
|------|-------------|
| HarmonyOS | Huawei's operating system |
| ArkTS | HarmonyOS official language, based on TypeScript |
| ArkUI | HarmonyOS declarative UI framework |
| DevEco Studio | HarmonyOS official IDE |
| HAP | HarmonyOS application package |
| @Component | Decorator for declaring a custom UI component |
| @State | Decorator for reactive state variables |

## FAQ

### Does it auto-publish apps?
No. v1 only helps with development, not publishing.

### Will it modify my code without asking?
Every change is explained first — which file, why, and what changes — and waits for your confirmation.

### Is my code uploaded to the cloud?
No. Your project files stay local. API calls go through your configured DeepSeek service.

### Where should I store my API key?
Only in your terminal environment variables (e.g. `~/.zshrc`). The repo only contains `.example` files.

---

> To get started: launch Claude Code and say "I want to build a xxx App."
