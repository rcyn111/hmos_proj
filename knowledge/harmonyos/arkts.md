# ArkTS 知识库

> 最后更新：2026-06-04
> ⚠️ 本文件不得包含 API key、token、密钥等敏感信息。

---

## 什么是 ArkTS？

ArkTS 是 HarmonyOS 官方推荐的开发语言。它基于 TypeScript 进行了扩展，增加了声明式 UI 的能力。

如果你会 TypeScript 或 JavaScript，ArkTS 的语法几乎一样，主要多了 UI 相关的装饰器。

---

## 基本语法

> 📝 **待补充**：首次使用时，Claw 会根据官方文档搜索并填充此部分。

---

## 装饰器（Decorator）

装饰器是 ArkTS 中最重要的概念之一。它们是写在类、方法或属性前面的 `@` 符号开头的标记。

### 常用装饰器

| 装饰器 | 用途 | 示例 |
|--------|------|------|
| @Entry | 标记一个页面（可被路由访问） | `@Entry @Component struct IndexPage {}` |
| @Component | 标记一个自定义组件 | `@Component struct MyButton {}` |
| @State | 声明组件内部状态（变了界面自动刷新） | `@State count: number = 0` |
| @Prop | 父组件传给子组件的属性（单向） | `@Prop title: string` |
| @Link | 父组件传给子组件的引用（双向绑定） | `@Link count: number` |
| @Provide | 向后代组件提供数据 | `@Provide theme: string = 'light'` |
| @Consume | 消费祖先组件提供的数据 | `@Consume theme: string` |
| @Watch | 监听状态变化并执行回调 | `@Watch('onChange') @State name: string` |

> 📝 **待补充**：每个装饰器的详细用法和代码示例。

---

## 数据类型

ArkTS 支持所有 TypeScript 基本类型：

```typescript
let name: string = 'Hello'
let count: number = 0
let isDone: boolean = false
let items: string[] = ['a', 'b', 'c']
let config: Record<string, number> = { a: 1, b: 2 }
```

---

## 函数

```typescript
// 普通函数
function add(a: number, b: number): number {
  return a + b
}

// 箭头函数
const multiply = (a: number, b: number): number => a * b
```

---

## 条件与循环

```typescript
// 条件判断
if (condition) {
  // ...
} else {
  // ...
}

// for 循环
for (let i = 0; i < items.length; i++) {
  console.log(items[i])
}

// for...of
for (const item of items) {
  console.log(item)
}
```

---

## 常见问题

> 📝 **待补充**：实际开发中遇到的 ArkTS 语法问题会记录在这里。

---

## 参考资料

- [HarmonyOS 官方文档 — ArkTS](https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/arkts-get-started)
