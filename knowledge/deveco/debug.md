# DevEco Studio 调试知识库

> 最后更新：2026-06-04
> ⚠️ 本文件不得包含 API key、token、密钥等敏感信息。

---

## 概述

调试就是让程序在运行过程中停下来，让你一行一行地看代码是怎么执行的，变量是什么值。

---

## 调试方式

### 1. 模拟器调试

在 DevEco Studio 中，使用内置模拟器运行和调试应用。

> 📝 **待补充**：
> - 如何启动模拟器
> - 如何设置断点
> - 如何查看变量值
> - 如何单步执行

### 2. 真机调试

通过 USB 连接真实的 HarmonyOS 手机进行调试。

> 📝 **待补充**：
> - 启用开发者模式
> - USB 调试配置
> - 签名配置

### 3. 日志输出

最简单的调试方式——在代码中打日志：

```typescript
import { hilog } from '@kit.PerformanceAnalysisKit'

hilog.info(0x0000, 'MyTag', '这是一条日志消息')
```

---

## 常见调试问题

> 📝 **待补充**：调试过程中的常见问题。

---

## 参考资料

- [HarmonyOS 官方文档 — 调试](https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/ide-debugging)
