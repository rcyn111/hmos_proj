/**
 * Index.ets — 键盘 UI / 玻璃光感皮肤
 *
 * ╔══════════════════════════════════════════════════════╗
 * ║  🎨 设计主题：沉浸光感 · 玻璃拟态                    ║
 * ║  Glass-morphism keyboard with light-sensing feel    ║
 * ║                                                     ║
 * ║  效果层次：                                          ║
 * ║  1. 底层：动态光感渐变背景（模拟光线从上方照射）       ║
 * ║  2. 中层：半透明玻璃质感按键 + 边缘光                 ║
 * ║  3. 顶层：按下时的光晕反馈                            ║
 * ╚══════════════════════════════════════════════════════╝
 *
 * 术语速查：
 * - backgroundBlurStyle：背景材质模糊，让组件背后内容变朦胧
 * - backgroundEffect：自定义背景材质（半径/饱和度/亮度）
 * - linearGradient：渐变色彩（模拟光线变化）
 * - shadow：组件阴影（深度感）
 * - opacity：透明度（玻璃感的关键）
 */

import keyboardCtrl from '../KeyboardController'
import { KeyData, KEYBOARD_LAYOUT } from '../model/KeyData'

// ╔══════════════════════════════════════════════════════╗
// ║         🎨 皮肤配置区（改这里调外观！）              ║
// ╚══════════════════════════════════════════════════════╝

// ===== 光感背景（模拟上方光源）=====
const BG_COLOR_START = '#2d1b69'    // 渐变顶部（深紫，暗处）
const BG_COLOR_MID = '#4a2c8a'      // 渐变中部（过渡）
const BG_COLOR_END = '#1a0a2e'      // 渐变底部（更深，阴影处）
const BG_COLOR_TOP_GLOW = '#6b3fb3' // 顶部光晕色（光源位置）

// ===== 玻璃按键 =====
const GLASS_BG = 'rgba(255, 255, 255, 0.08)'  // 玻璃底色（白 + 低透明度）
const GLASS_BORDER = 'rgba(255, 255, 255, 0.18)' // 玻璃边框（模拟边缘反光）
const GLASS_TEXT = '#f0e6ff'          // 玻璃上的文字色
const GLASS_RADIUS = 14               // 按键圆角
const GLASS_SHADOW_RADIUS = 8         // 按键阴影半径
const GLASS_SHADOW_COLOR = 'rgba(0, 0, 0, 0.3)' // 阴影色

// ===== 按键按下（光晕反馈）=====
const PRESS_BG = 'rgba(180, 140, 255, 0.35)'   // 按下时的发光底色
const PRESS_GLOW_RADIUS = 20                    // 按下时阴影扩散（光晕）
const PRESS_GLOW_COLOR = 'rgba(160, 120, 255, 0.5)' // 按下光晕颜色
const PRESS_SCALE = 0.93                        // 按下缩放

// ===== 特殊功能键（删除、空格等）=====
const SPECIAL_GLASS_BG = 'rgba(255, 255, 255, 0.04)'
const SPECIAL_GLASS_TEXT = '#c8b8e8'

// ===== 尺寸 =====
const KEY_HEIGHT = 56
const KEY_MARGIN = 4
const KEY_FONT_SIZE = 20
const KEYBOARD_PADDING_H = 8
const KEYBOARD_PADDING_V = 10

// ╔══════════════════════════════════════════════════════╗
// ║              页面主体（不要改下面！）                 ║
// ╚══════════════════════════════════════════════════════╝

@Entry
@Component
struct KeyboardPage {
  @State pressedKey: string = ''

  build() {
    // ----- 最外层：光感渐变背景 -----
    Stack() {
      // 层 1：主渐变背景
      Column()
        .width('100%')
        .height('100%')
        .linearGradient({
          direction: GradientDirection.Top,
          colors: [
            [BG_COLOR_TOP_GLOW, 0.0],   // 顶部光晕（光源）
            [BG_COLOR_START, 0.25],      // 上段
            [BG_COLOR_MID, 0.55],        // 中段
            [BG_COLOR_END, 1.0]          // 底部暗区
          ]
        })

      // 层 2：键盘按键区
      Column() {
        ForEach(KEYBOARD_LAYOUT, (row: KeyData[], rowIndex: number) => {
          Row() {
            ForEach(row, (key: KeyData) => {
              // ===== 单个玻璃按键 =====
              Button() {
                Text(key.label)
                  .fontSize(KEY_FONT_SIZE)
                  .fontWeight(key.type === 'special' ? FontWeight.Medium : FontWeight.Regular)
                  .fontColor(key.type === 'normal' ? GLASS_TEXT : SPECIAL_GLASS_TEXT)
              }
              // --- 玻璃外观 ---
              .backgroundColor(
                this.pressedKey === `${rowIndex}-${key.label}`
                  ? PRESS_BG
                  : (key.type === 'normal' ? GLASS_BG : SPECIAL_GLASS_BG)
              )
              .borderRadius(GLASS_RADIUS)
              .border({
                width: 0.5,
                color: GLASS_BORDER,
                style: BorderStyle.Solid
              })
              // --- 玻璃背景模糊（让背后渐变朦胧透出）---
              .backgroundBlurStyle(BlurStyle.Thin, {
                colorMode: ThemeColorMode.DARK,
                adaptiveColor: AdaptiveColor.DEFAULT,
                scale: 0.7
              })
              // --- 阴影（立体 / 光晕）---
              .shadow({
                radius: this.pressedKey === `${rowIndex}-${key.label}`
                  ? PRESS_GLOW_RADIUS : GLASS_SHADOW_RADIUS,
                color: this.pressedKey === `${rowIndex}-${key.label}`
                  ? PRESS_GLOW_COLOR : GLASS_SHADOW_COLOR,
                offsetX: 0,
                offsetY: this.pressedKey === `${rowIndex}-${key.label}` ? 0 : 2
              })
              // --- 按下缩放 ---
              .scale(
                this.pressedKey === `${rowIndex}-${key.label}`
                  ? { x: PRESS_SCALE, y: PRESS_SCALE }
                  : { x: 1, y: 1 }
              )
              // --- 动画 ---
              .animation({ duration: 120, curve: Curve.EaseOut })
              // --- 尺寸 ---
              .width(`${100 / row.length * key.flex}%`)
              .height(KEY_HEIGHT)
              .margin(KEY_MARGIN)
              // --- 事件 ---
              .onTouch((event: TouchEvent) => {
                const keyId = `${rowIndex}-${key.label}`
                if (event.type === TouchType.Down) {
                  this.pressedKey = keyId
                } else if (event.type === TouchType.Up) {
                  this.pressedKey = ''
                  this.onKeyPress(key)
                }
              })
            })
          }
          .width('100%')
          .padding({
            left: KEYBOARD_PADDING_H,
            right: KEYBOARD_PADDING_H,
            top: 2,
            bottom: 2
          })
        })
      }
      .width('100%')
      .height('100%')
      .justifyContent(FlexAlign.Center)
      .padding({
        top: KEYBOARD_PADDING_V,
        bottom: KEYBOARD_PADDING_V
      })
      // --- 键盘区整体微模糊（让按键与背景融合更自然）---
      .backgroundBlurStyle(BlurStyle.COMPONENT_ULTRA_THIN, {
        colorMode: ThemeColorMode.DARK,
        scale: 0.4
      })
    }
    .width('100%')
    .height('100%')
  }

  /**
   * 按键按下 → 执行输入操作
   */
  private onKeyPress(key: KeyData): void {
    if (key.value.length > 0) {
      keyboardCtrl.insertText(key.value)
    } else if (key.label === '⌫') {
      keyboardCtrl.deleteForward()
    } else if (key.label === '↵') {
      keyboardCtrl.insertText('\n')
    }
  }
}
