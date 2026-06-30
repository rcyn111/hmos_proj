# 路由知识库

> 最后更新：2026-06-04
> ⚠️ 本文件不得包含 API key、token、密钥等敏感信息。

---

## 什么是路由？

路由就是页面跳转。比如从首页点击一个按钮，跳转到详情页。

HarmonyOS 提供两种路由方式：
1. **router API**（传统方式，简单直接）
2. **Navigation 组件**（新方式，更灵活，推荐）

---

## 方式一：router API

### 基本跳转

```typescript
import { router } from '@kit.ArkUI'

// 跳转到指定页面
router.pushUrl({ url: 'pages/DetailPage' })

// 返回上一页
router.back()
```

### 带参数跳转

> 📝 **待补充**：带参数的跳转方式。

### 清空历史跳转（如登录后跳首页）

> 📝 **待补充**：replaceUrl 用法。

---

## 方式二：Navigation 组件（推荐）

> 📝 **待补充**：Navigation + NavPathStack 的完整用法。

---

## 页面配置

页面必须在 `entry/src/main/resources/base/profile/main_pages.json` 中注册：

```json
{
  "src": [
    "pages/Index",
    "pages/DetailPage"
  ]
}
```

---

## 常见问题

> 📝 **待补充**：路由相关的报错和解决方案。

---

## 参考资料

- [HarmonyOS 官方文档 — 页面路由](https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/arkts-routing)
