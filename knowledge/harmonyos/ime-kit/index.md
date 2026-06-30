# IME Kit — 输入法开发知识库

> 最后更新：2026-06-04
> 来源：华为官方文档 + 社区实战文章
> 可信度：高（基于官方文档）
> ⚠️ 本文件不得包含 API key、token、密钥等敏感信息。

---

## 什么是 IME Kit？

IME Kit（输入法开发服务）是 HarmonyOS 提供的输入法框架。它建立输入框和输入法 App 之间的通信通道，让你可以创建自定义键盘。

---

## 核心架构（三层）

```
系统输入法框架（IME Kit）
    └── 你的 InputMethodExtensionAbility
        ├── KeyboardController（逻辑控制）
        └── Panel + ArkUI 页面（键盘 UI / "皮肤"）
```

| 组件 | 作用 |
|------|------|
| InputMethodExtensionAbility | 输入法入口，系统通过它启动你的键盘 |
| InputMethodAbility | 输入法核心对象，负责创建 Panel、监听事件 |
| Panel | 键盘的窗口容器，里面放 ArkUI 页面 |
| InputClient | 与目标输入框通信（插入/删除文字） |
| InputMethodSubtype | 子类型配置（英文键盘/中文键盘/数字键盘切换） |

---

## 关键 API

```typescript
import { InputMethodExtensionAbility, inputMethodEngine } from '@kit.IMEKit'

// 获取输入法能力对象
inputMethodEngine.getInputMethodAbility((err, ability) => { ... })

// 创建键盘面板
ability.createPanel(context, { type: TYPE_INPUT_METHOD, flag: FLAG_FIXED })

// 监听事件
ability.on('inputStart', (kbController, client) => { ... })  // 键盘激活
ability.on('inputStop', () => { ... })                        // 键盘隐藏
ability.on('setSubtype', (subtype) => { ... })                // 子类型切换

// 文本操作
client.insertText('hello')    // 插入文字
client.deleteForward(1)       // 删除光标前 1 个字符
```

---

## 项目配置要点

### module.json5
```json5
{
  "extensionAbilities": [{
    "type": "inputMethod",          // 必须
    "exported": true,               // 必须，否则不出现在系统输入法列表
    "metadata": [{
      "name": "ohos.extension.input_method",
      "resource": "$profile:input_method_config"
    }]
  }],
  "requestPermissions": [{
    "name": "ohos.permission.CONNECT_IME_ABILITY"  // 必须
  }]
}
```

### 子类型配置（input_method_config.json）
```json
{
  "subtypes": [{
    "id": "en_us",
    "label": "English Keyboard",
    "locale": "en-US",
    "mode": "lower"
  }]
}
```

---

## 注意事项

⚠️ **部分 HarmonyOS NEXT 版本可能暂不支持 InputMethod ExtensionAbility**
- 开发前确认 DevEco Studio 中 `New → Extension Ability → InputMethod` 是否可用
- 当前 SDK 是否包含 IME Kit 支持

⚠️ **输入法需要真机测试，模拟器可能不支持**

⚠️ **Panel 类型**：
- `FLAG_FIXED`：固定键盘（常规输入法）
- `FLAG_FLOATING`：浮动键盘

---

## 参考资料

- [IME Kit 官方介绍](https://developer.huawei.com/consumer/cn/doc/harmonyos-guides-V13/ime-kit-intro-V13)
- [InputMethodExtensionAbility API](https://developer.huawei.com/consumer/cn/doc/harmonyos-references-v5/js-apis-inputmethod-extension-ability-V5)
- [输入法子类型开发指南](https://developer.huawei.com/consumer/cn/doc/harmonyos-guides-V14/input-method-subtype-guide-V14)
- [输入法开发实战笔记（博客）](https://www.cnblogs.com/yihonghh/p/19302691)
- [鸿蒙输入法开发指南（SegmentFault）](https://segmentfault.com/a/1190000046819854)
