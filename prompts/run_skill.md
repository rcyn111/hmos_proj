# Skill 执行提示词模板

> 用途：当需要手动触发某个 skill 时使用的提示词。

---

## 模板

```
请使用 {skill-name} skill 帮我完成以下任务。

## 任务描述
{任务描述}

## 相关文件
- {文件路径 1}
- {文件路径 2}

## 额外要求
{如果有特殊要求}

## 执行要求
- 按照 .claude/skills/{skill-name}/SKILL.md 中定义的步骤执行
- 每完成一步向我汇报
- 修改文件前先确认
- 执行完成后生成 runs/ 复盘记录
```

---

## Skill 名称速查

| Skill | 触发关键词 |
|-------|-----------|
| harmony-requirement-analyzer | "分析需求"、"规划项目" |
| harmony-doc-searcher | "搜索资料"、"查一下 API" |
| harmony-arkui-page-builder | "创建页面"、"生成页面代码" |
| harmony-error-fixer | "修复报错"、"帮我看看这个错误" |
| harmony-code-reviewer | "审查代码"、"检查代码质量" |
| harmony-skill-evolver | "优化 skill"（通常自动触发） |
