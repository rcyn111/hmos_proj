/**
 * KeyData.ts — 键盘按键数据模型
 *
 * 这个文件定义键盘上每个按键的数据结构。
 * 修改 KEYBOARD_LAYOUT 数组可以改变按键排布。
 */

/** 单个按键的数据 */
export class KeyData {
  /** 按键显示的文字 */
  label: string
  /** 按下时插入的文本（空字符串 = 功能键，如删除） */
  value: string
  /**
   * 按键类型：
   * - 'normal'  = 普通字母键
   * - 'special' = 特殊功能键（删除、空格、换行）
   */
  type: 'normal' | 'special'
  /** 按键宽度权重（1 = 标准宽度，数字越大越宽） */
  flex: number

  constructor(label: string, value: string, type: 'normal' | 'special', flex: number = 1) {
    this.label = label
    this.value = value
    this.type = type
    this.flex = flex
  }
}

/**
 * QWERTY 键盘布局（4 行）
 *
 * 📝 想改按键排布？直接改下面 4 个数组即可。
 *    每个 KeyData(label, value, type, flex)
 *    - label: 按键上显示的字
 *    - value: 按下去后实际输入的文本
 *    - type:  'normal' 或 'special'
 *    - flex:  宽度比例，1=标准
 */
export const KEYBOARD_LAYOUT: KeyData[][] = [
  // 第 1 行
  [
    new KeyData('q', 'q', 'normal'),
    new KeyData('w', 'w', 'normal'),
    new KeyData('e', 'e', 'normal'),
    new KeyData('r', 'r', 'normal'),
    new KeyData('t', 't', 'normal'),
    new KeyData('y', 'y', 'normal'),
    new KeyData('u', 'u', 'normal'),
    new KeyData('i', 'i', 'normal'),
    new KeyData('o', 'o', 'normal'),
    new KeyData('p', 'p', 'normal'),
  ],
  // 第 2 行
  [
    new KeyData('a', 'a', 'normal'),
    new KeyData('s', 's', 'normal'),
    new KeyData('d', 'd', 'normal'),
    new KeyData('f', 'f', 'normal'),
    new KeyData('g', 'g', 'normal'),
    new KeyData('h', 'h', 'normal'),
    new KeyData('j', 'j', 'normal'),
    new KeyData('k', 'k', 'normal'),
    new KeyData('l', 'l', 'normal'),
  ],
  // 第 3 行
  [
    new KeyData('⇧', '', 'special'), // Shift（暂不实现功能）
    new KeyData('z', 'z', 'normal'),
    new KeyData('x', 'x', 'normal'),
    new KeyData('c', 'c', 'normal'),
    new KeyData('v', 'v', 'normal'),
    new KeyData('b', 'b', 'normal'),
    new KeyData('n', 'n', 'normal'),
    new KeyData('m', 'm', 'normal'),
    new KeyData('⌫', '', 'special', 1.2), // 删除键，稍宽
  ],
  // 第 4 行（空格行）
  [
    new KeyData(',', ',', 'normal'),
    new KeyData(' ', ' ', 'special', 5), // 空格键，5 倍宽度
    new KeyData('.', '.', 'normal'),
    new KeyData('↵', '\n', 'special', 1.5), // 换行键
  ],
]
