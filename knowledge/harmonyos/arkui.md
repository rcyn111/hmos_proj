# ArkUI 知识库

> 最后更新：2026-06-04
> ⚠️ 本文件不得包含 API key、token、密钥等敏感信息。

---

## 什么是 ArkUI？

ArkUI 是 HarmonyOS 的声明式 UI 框架。你可以用类似写配置的方式描述界面，状态变化时界面会自动更新。

---

## 基本页面结构

一个最简单的 ArkUI 页面长这样：

```typescript
// 文件名：Index.ets
@Entry          // @Entry：表示这是一个页面入口
@Component      // @Component：表示这是一个组件
struct Index {  // struct：组件必须定义为 struct
  @State message: string = 'Hello HarmonyOS'  // @State：状态变量，变了界面自动刷新

  build() {     // build()：描述界面长什么样（必须实现）
    Column() {  // Column：垂直排列子组件
      Text(this.message)    // Text：显示文本
        .fontSize(30)       // .fontSize()：设置字体大小（链式调用）
        .fontWeight(FontWeight.Bold)
    }
    .width('100%')   // 设置 Column 宽度为满屏
    .height('100%')  // 设置 Column 高度为满屏
  }
}
```

---

## 常用布局组件

### Column — 垂直布局
子组件从上到下排列。

```typescript
Column() {
  Text('第一行')
  Text('第二行')
  Text('第三行')
}
```

### Row — 水平布局
子组件从左到右排列。

```typescript
Row() {
  Text('左边')
  Text('中间')
  Text('右边')
}
```

### Flex — 弹性布局
比 Column/Row 更灵活的布局方式。

> 📝 **待补充**：Flex 详细用法。

### Grid — 网格布局

> 📝 **待补充**：Grid 详细用法。

---

## 常用基础组件

| 组件 | 用途 | 基本用法 |
|------|------|---------|
| Text | 显示文本 | `Text('内容').fontSize(16)` |
| Button | 按钮 | `Button('点击我').onClick(() => {})` |
| TextInput | 输入框 | `TextInput({ placeholder: '请输入' })` |
| Image | 图片 | `Image($r('app.media.icon'))` |
| List | 列表 | `List() { ForEach(...) }` |
| ListItem | 列表项 | `ListItem() { Text('一项') }` |
| Checkbox | 复选框 | `Checkbox().onChange((value) => {})` |
| Toggle | 开关 | `Toggle({ type: ToggleType.Switch })` |
| Slider | 滑动条 | `Slider({ value: 0, min: 0, max: 100 })` |
| Progress | 进度条 | `Progress({ value: 50 })` |
| LoadingProgress | 加载动画 | `LoadingProgress()` |

---

## 状态管理

ArkUI 最重要的概念之一。简单理解：**变量变了，界面自动变**。

| 装饰器 | 作用域 | 传递方向 |
|--------|--------|---------|
| @State | 本组件内部 | — |
| @Prop | 子组件接收 | 父 → 子（单向） |
| @Link | 子组件接收 | 父 ↔ 子（双向） |
| @Provide | 向后代提供 | 祖 → 任意后代 |
| @Consume | 从祖先获取 | 任意后代 ← 祖 |

> 📝 **待补充**：每种状态管理的代码示例。

---

## 页面导航（路由）

```typescript
// 跳转到新页面
import { router } from '@kit.ArkUI'

router.pushUrl({ url: 'pages/DetailPage' })

// 返回上一页
router.back()
```

> 📝 **待补充**：带参数跳转、Navigation 组件的用法。

---

## 常见问题

> 📝 **待补充**：开发中遇到的 ArkUI 使用问题。

---

## 参考资料

- [HarmonyOS 官方文档 — ArkUI](https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/arkui-overview)
- [ArkUI 组件列表](https://developer.huawei.com/consumer/cn/doc/harmonyos-references/ts-components-summary)
