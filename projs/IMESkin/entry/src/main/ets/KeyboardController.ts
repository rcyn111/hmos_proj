/**
 * KeyboardController.ts — 键盘逻辑控制器
 *
 * 这个文件负责键盘的"大脑"部分：
 * 1. 创建键盘窗口（Panel）
 * 2. 监听输入事件（用户点开输入框时显示键盘）
 * 3. 处理文本操作（插入文字、删除文字）
 *
 * 和 UI（Index.ets）的关系：
 * - 本文件管逻辑（"做什么"）
 * - Index.ets 管外观（"长什么样"）
 */

import { inputMethodEngine } from '@kit.IMEKit'
import { window } from '@kit.ArkUI'
import { BusinessError } from '@kit.BasicServicesKit'

// ---------- 类型定义 ----------

/** 输入法引擎提供的能力对象 */
type InputMethodAbility = Parameters<
  Parameters<typeof inputMethodEngine.getInputMethodAbility>['0']
>['0']

/** 键盘控制器对象（由 inputStart 事件传入） */
type KeyboardController = Parameters<
  Parameters<InputMethodAbility['on']>['1']
>['0']

/** 输入客户端对象（负责与目标输入框通信） */
type InputClient = Parameters<
  Parameters<InputMethodAbility['on']>['1']
>['1']

// ---------- 皮肤配置（用户可以修改这里！）----------

/** 键盘高度（单位：vp，虚拟像素） */
const KEYBOARD_HEIGHT = 280

// ---------- 控制器类 ----------

export class KeyboardController {
  /** 键盘 UI 所在的窗口面板 */
  private panel: window.Panel | null = null

  /** 当前连接的输入客户端 */
  private client: InputClient | null = null

  /** 输入法 Engine 实例 */
  private imeAbility: InputMethodAbility | null = null

  /**
   * 输入法启动时调用
   */
  onCreate(context: InputMethodExtensionAbility['context']): void {
    // 1. 获取输入法引擎能力
    inputMethodEngine.getInputMethodAbility((err: BusinessError, ability: InputMethodAbility) => {
      if (err) {
        console.error('[IMESkin] 获取输入法能力失败:', JSON.stringify(err))
        return
      }
      this.imeAbility = ability
      this.setupPanel(context)
      this.listenEvents()
    })
  }

  /**
   * 创建键盘面板窗口
   */
  private setupPanel(context: InputMethodExtensionAbility['context']): void {
    if (!this.imeAbility) return

    const panelInfo: window.PanelInfo = {
      type: window.PanelType.TYPE_INPUT_METHOD,
      flag: window.PanelFlag.FLAG_FIXED // 固定式键盘（非浮动）
    }

    this.imeAbility.createPanel(context, panelInfo).then((panel: window.Panel) => {
      this.panel = panel
      // 设置键盘大小
      panel.resize(window.RectSize.empty().width, KEYBOARD_HEIGHT)
      // 加载键盘 UI（"皮肤"所在文件）
      panel.setUiContent('pages/Index', (err: BusinessError) => {
        if (err) {
          console.error('[IMESkin] 加载键盘 UI 失败:', JSON.stringify(err))
          return
        }
        console.info('[IMESkin] 键盘 UI 加载成功')
      })
    }).catch((err: BusinessError) => {
      console.error('[IMESkin] 创建面板失败:', JSON.stringify(err))
    })
  }

  /**
   * 监听输入法事件
   */
  private listenEvents(): void {
    if (!this.imeAbility) return

    // 用户点击输入框 → 显示键盘
    this.imeAbility.on('inputStart', (kbController: KeyboardController, client: InputClient) => {
      console.info('[IMESkin] 键盘已激活 — 用户正在输入')
      this.client = client
      // 显示键盘面板
      if (this.panel) {
        this.panel.show()
      }
    })

    // 用户关闭输入框 → 隐藏键盘
    this.imeAbility.on('inputStop', () => {
      console.info('[IMESkin] 键盘已隐藏')
      this.client = null
      if (this.panel) {
        this.panel.hide()
      }
    })
  }

  // ---------- 文本操作方法（给 UI 层调用）----------

  /**
   * 插入文本（按下字母键时调用）
   * @param text — 要插入的文字
   */
  insertText(text: string): void {
    if (!this.client) {
      console.warn('[IMESkin] 无输入目标，无法插入')
      return
    }
    this.client.insertText(text, (err: BusinessError) => {
      if (err) {
        console.error('[IMESkin] 插入文本失败:', JSON.stringify(err))
      }
    })
  }

  /**
   * 删除一个字符（按下删除键时调用）
   */
  deleteForward(): void {
    if (!this.client) {
      console.warn('[IMESkin] 无输入目标，无法删除')
      return
    }
    this.client.deleteForward(1, (err: BusinessError) => {
      if (err) {
        console.error('[IMESkin] 删除失败:', JSON.stringify(err))
      }
    })
  }

  /**
   * 输入法销毁时清理
   */
  onDestroy(): void {
    this.client = null
    this.panel = null
    this.imeAbility = null
    console.info('[IMESkin] 资源已释放')
  }
}

// 导出单例供 InputMethodService 和 Index.ets 使用
export default new KeyboardController()
