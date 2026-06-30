/**
 * EntryAbility.ets — 应用入口
 *
 * 虽然是输入法 App，但 HarmonyOS 要求每个 App 至少有一个
 * 普通的 Ability 作为启动入口。
 *
 * 这个文件不需要改，保持默认即可。
 */

import { UIAbility, Want } from '@kit.AbilityKit'
import { hilog } from '@kit.PerformanceAnalysisKit'
import { window } from '@kit.ArkUI'

export default class EntryAbility extends UIAbility {
  onCreate(want: Want, launchParam: Record<string, number>): void {
    hilog.info(0x0000, 'IMESkin', '应用已创建')
  }

  onDestroy(): void {
    hilog.info(0x0000, 'IMESkin', '应用已销毁')
  }

  onWindowStageCreate(windowStage: window.WindowStage): void {
    hilog.info(0x0000, 'IMESkin', '窗口已创建')
    windowStage.loadContent('pages/Index', (err) => {
      if (err.code) {
        hilog.error(0x0000, 'IMESkin', '加载页面失败: %{public}s', JSON.stringify(err))
        return
      }
      hilog.info(0x0000, 'IMESkin', '页面加载成功')
    })
  }

  onWindowStageDestroy(): void {
    hilog.info(0x0000, 'IMESkin', '窗口已销毁')
  }
}
