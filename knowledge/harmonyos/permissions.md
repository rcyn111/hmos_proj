# 权限知识库

> 最后更新：2026-06-04
> ⚠️ 本文件不得包含 API key、token、密钥等敏感信息。

---

## 概述

HarmonyOS 应用访问敏感能力（如相机、麦克风、通讯录等）需要先申请权限。

---

## 权限分类

### 系统授权（user_grant 权限）
需要用户在弹窗中确认的权限：
- 相机、麦克风、通讯录、日历、位置等

### 无需授权（system_grant 权限）
系统自动授权的权限：
- 网络访问、振动等

---

## 申请权限步骤

> 📝 **待补充**：
> 1. 在 `module.json5` 中声明权限
> 2. 在代码中调用 `requestPermissionsFromUser`
> 3. 处理用户拒绝的情况

---

## 常见权限列表

| 权限 | 说明 |
|------|------|
| ohos.permission.INTERNET | 网络访问 |
| ohos.permission.CAMERA | 相机 |
| ohos.permission.MICROPHONE | 麦克风 |
| ohos.permission.LOCATION | 位置 |
| ohos.permission.READ_MEDIA | 读取媒体文件 |
| ohos.permission.WRITE_MEDIA | 写入媒体文件 |

---

## 常见问题

> 📝 **待补充**：权限相关的报错和解决方案。

---

## 参考资料

- [HarmonyOS 官方文档 — 权限](https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/security-permissions)
