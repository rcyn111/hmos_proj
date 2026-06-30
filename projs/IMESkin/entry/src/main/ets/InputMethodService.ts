/**
 * InputMethodService.ts — 输入法入口
 *
 * 这个文件是输入法的"大门"。当用户在系统设置中启用你的输入法时，
 * HarmonyOS 会调用这个类来启动你的键盘。
 *
 * 这里的代码非常简洁，因为具体逻辑都交给 KeyboardController 处理。
 */

import { InputMethodExtensionAbility } from '@kit.IMEKit'
import { Want } from '@kit.AbilityKit'
import { KeyboardController } from './KeyboardController'

// 全局唯一键盘控制器实例
const keyboardCtrl = new KeyboardController()

export default class InputMethodService extends InputMethodExtensionAbility {

  /**
   * 输入法被创建时调用（用户启用了你的输入法）
   * @param want — 系统传入的启动参数
   */
  onCreate(want: Want): void {
    console.info('[IMESkin] 输入法服务已创建')
    keyboardCtrl.onCreate(this.context)
  }

  /**
   * 输入法被销毁时调用（用户切换输入法或关闭了你的输入法）
   */
  onDestroy(): void {
    console.info('[IMESkin] 输入法服务已销毁')
    keyboardCtrl.onDestroy()
  }
}
