#!/bin/bash
# ============================================================
# HarmonyOS Dev Claw — 项目初始化脚本
# ============================================================
# 用途：验证项目目录结构是否完整，检查必要文件是否存在。
# 使用：bash scripts/init_project.sh
# ============================================================

set -e

PROJECT_ROOT="/Users/renchengtian/Projects/hmos_proj"

echo "========================================="
echo " HarmonyOS Dev Claw — 项目初始化检查"
echo "========================================="
echo ""

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_item() {
    local path="$1"
    local desc="$2"
    if [ -e "$path" ]; then
        echo -e "  ${GREEN}✓${NC} $desc"
        return 0
    else
        echo -e "  ${RED}✗${NC} $desc — 缺失！"
        return 1
    fi
}

FAIL_COUNT=0

echo "--- 核心文件 ---"
check_item "$PROJECT_ROOT/CLAUDE.md" "CLAUDE.md 工作规则" || ((FAIL_COUNT++))
check_item "$PROJECT_ROOT/README.md" "README.md 使用说明" || ((FAIL_COUNT++))

echo ""
echo "--- config/ ---"
check_item "$PROJECT_ROOT/config/dsapi.env.example" "DSAPI 配置示例" || ((FAIL_COUNT++))
check_item "$PROJECT_ROOT/config/permissions.md" "权限规则" || ((FAIL_COUNT++))
check_item "$PROJECT_ROOT/config/claw_config.yaml" "Claw 行为配置" || ((FAIL_COUNT++))

echo ""
echo "--- docs/ ---"
check_item "$PROJECT_ROOT/docs/PRODUCT.md" "产品定义" || ((FAIL_COUNT++))
check_item "$PROJECT_ROOT/docs/ROADMAP.md" "路线图" || ((FAIL_COUNT++))
check_item "$PROJECT_ROOT/docs/ARCHITECTURE.md" "架构说明" || ((FAIL_COUNT++))
check_item "$PROJECT_ROOT/docs/USAGE.md" "使用指南" || ((FAIL_COUNT++))

echo ""
echo "--- .claude/skills/ ---"
check_item "$PROJECT_ROOT/.claude/skills/harmony-requirement-analyzer/SKILL.md" "需求分析器" || ((FAIL_COUNT++))
check_item "$PROJECT_ROOT/.claude/skills/harmony-doc-searcher/SKILL.md" "文档搜索器" || ((FAIL_COUNT++))
check_item "$PROJECT_ROOT/.claude/skills/harmony-arkui-page-builder/SKILL.md" "页面生成器" || ((FAIL_COUNT++))
check_item "$PROJECT_ROOT/.claude/skills/harmony-error-fixer/SKILL.md" "报错修复器" || ((FAIL_COUNT++))
check_item "$PROJECT_ROOT/.claude/skills/harmony-code-reviewer/SKILL.md" "代码审查器" || ((FAIL_COUNT++))
check_item "$PROJECT_ROOT/.claude/skills/harmony-skill-evolver/SKILL.md" "Skill 进化器" || ((FAIL_COUNT++))

echo ""
echo "--- knowledge/ ---"
check_item "$PROJECT_ROOT/knowledge/harmonyos/arkts.md" "ArkTS 知识库" || ((FAIL_COUNT++))
check_item "$PROJECT_ROOT/knowledge/harmonyos/arkui.md" "ArkUI 知识库" || ((FAIL_COUNT++))
check_item "$PROJECT_ROOT/knowledge/harmonyos/common_errors.md" "常见错误（鸿蒙）" || ((FAIL_COUNT++))
check_item "$PROJECT_ROOT/knowledge/deveco/common_errors.md" "常见错误（IDE）" || ((FAIL_COUNT++))

echo ""
echo "--- 目录检查 ---"
check_item "$PROJECT_ROOT/runs" "runs/ 目录" || ((FAIL_COUNT++))
check_item "$PROJECT_ROOT/memory" "memory/ 目录" || ((FAIL_COUNT++))
check_item "$PROJECT_ROOT/projs" "projs/ 目录" || ((FAIL_COUNT++))
check_item "$PROJECT_ROOT/scripts" "scripts/ 目录" || ((FAIL_COUNT++))
check_item "$PROJECT_ROOT/prompts" "prompts/ 目录" || ((FAIL_COUNT++))

echo ""
echo "========================================="
if [ $FAIL_COUNT -eq 0 ]; then
    echo -e " ${GREEN}✓ 检查通过！所有必要文件就绪。${NC}"
else
    echo -e " ${RED}✗ 检查未通过！缺失 $FAIL_COUNT 个文件/目录。${NC}"
fi
echo "========================================="

exit $FAIL_COUNT
