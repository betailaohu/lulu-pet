# iOS 端实施说明

## 当前状态

**工程骨架已完整写好**，但**没有在 Xcode 里编译过**——本机是 Windows，没有 Mac / Xcode。把它拷到 Mac 上，装 XcodeGen 后一条命令生成 `.xcodeproj` 就能打开；没有 Mac 就走 GitHub Actions（见下）。

**要出装到 iPhone 的包、以及 iOS 26.6.1 / iPhone 17 的适配细节，看 [`打包与安装指南.md`](打包与安装指南.md)。**

iOS 上**做不了全局悬浮窗**（沙盒限制）。采用的形态是：**主 App 完整互动 + 桌面/锁屏小组件 + 灵动岛 Live Activity**，与 Android 共用同一套素材和同一份状态配置。

> **用免费 Apple ID 侧载时，包里默认不带小组件与灵动岛。**
> 因为免费账号只能给主 App 建 profile（内嵌 `PetWidget.appex` 会让重签失败），也拿不到 App Groups（小组件读不到数值）。
> CI 默认调用 `scripts/make_apponly_project.py` 生成只含 `PetApp` 的 spec；有付费开发者账号时用原始 `project.yml` 出全量包。

## 架构修正（重要）

早先规划写的是「三个 target」，实际应该是 **2 个 target**：

| target | 类型 | 内容 |
| --- | --- | --- |
| `PetApp` | application | SwiftUI 主 App、PetState 状态机、互动视图 |
| `PetWidget` | app-extension | WidgetKit 小组件 **+ Live Activity** |

Apple 要求 Live Activity 的 UI 由 Widget Extension 里的 `ActivityConfiguration` 提供，**不能单独建一个 extension**。`PetLiveActivity/` 只是代码目录，被两个 target 一起编译（`project.yml` 里已配置）。

两个 target 共用同一个 App Group `group.com.lulu.pet`，entitlements 里 identifier 必须完全一致——写错是最常见的「小组件一片空白」原因。

## Mac 上三步跑起来

```
brew install xcodegen
cd ios
xcodegen generate
open LuluPet.xcodeproj
```

然后：两个 target 都选你的 Development Team（自动签名）→ 选真机或模拟器 → Run。

首次编译前确认：

- `Resources/Frames/` 里 36 张 `frame-*.png` 在（已由 `sync_assets.py` 同步）
- `Resources/manifest.json` / `state.json` 在（已同步）
- `Resources/Assets.xcassets/AppIcon.appiconset/` 里 1024 图标在（已生成）
- 两个 entitlements 都含 `group.com.lulu.pet`
- 部署目标 **iOS 17.0**（`containerBackground` 与 Live Activity 都要求 ≥17 才不用写一堆 `#available`）

替换正式立绘后，在仓库根目录重跑同步即可，双端素材一起更新：

```
python assets/lulu/sync_assets.py
```

## 目录结构（已落地）

```
ios/
├── project.yml                  # XcodeGen：2 个 target、显式 scheme、部署目标 17.0
├── README.md
├── 打包与安装指南.md             # 没 Mac 也能出 ipa + Sideloadly 装机步骤
├── Shared/                      # 两个 target 都编译
│   ├── AppGroup.swift           # App Group 快照读写（拿不到 suite 时退化到 .standard）
│   └── PetManifest.swift        # manifest.json 的 Codable 读取器
├── PetApp/
│   ├── App/LuluApp.swift        # @main
│   ├── Views/PetView.swift      # 状态立绘 + 呼吸动画 + 摸头/喂食 + 右上角齿轮
│   ├── Views/SettingsView.swift # 设置页：三条数值 / 共享通道状态 / 重置
│   ├── State/PetState.swift     # 养成状态机（对齐 Android PetState.kt）
│   ├── Info.plist
│   └── PetApp.entitlements
├── PetWidget/
│   ├── LuluWidget.swift         # WidgetBundle + TimelineProvider + 三种尺寸视图
│   ├── Info.plist
│   └── PetWidget.entitlements
├── PetLiveActivity/
│   └── PetLiveActivity.swift    # ActivityAttributes + 灵动岛四种呈现 + Manager
└── Resources/
    ├── Frames/frame-*.png       # 36 张（与 Android 同一套）
    ├── Assets.xcassets/         # AppIcon（由 frame-neutral.png 合成）
    ├── manifest.json
    └── state.json
```

## 已实现的功能

- **主 App**：读 `shared/*.json`，状态立绘切换 + 呼吸位移；点击摸头（`pat`）、喂食（`feed`）、三条数值进度条；台词气泡按 `duration` 自动收回待机帧；右上角齿轮进设置页。
- **设置页**：三条数值明细 + App Group 共享通道是否可用 + 手动刷新小组件 / 结束灵动岛 / 数值重置。
- **状态机**：饱食度 / 心情按小时衰减、亲密度每日上限、低阈值插队行为、`statusText` 文案来自 `state.json`，语义与 Android 对齐。
- **小组件**：small / medium / 锁屏 accessory（circular / rectangular / inline）五种呈现；静态立绘 + 状态文案 + 数值条；Timeline 15 分钟请求一次（实际刷新由系统调度）。
- **灵动岛**：compact / minimal / expanded / 锁屏四种呈现；设了 30 分钟 `staleDate`，避免做成永不结束的常驻活动（审核风险）。
- **数据同步**：状态变化 → 写 App Group → `WidgetCenter.reloadAllTimelines()` → 更新 Live Activity。

## 平台限制（必须遵守）

| 限制 | 影响 |
| --- | --- |
| Widget 是系统渲染的**静态快照**，扩展不常驻 | 不能连续播帧动画；靠 Timeline 条目切换状态 |
| 动画上限 **2 秒**，仅用于内容变化过渡 | 别设计「小组件里走路的水豚」 |
| 刷新由系统调度，典型 40–70 次 / 24h | 15 分钟只是「最早再次请求」，系统可能延后 |
| Always-On 显示会抑制动画 | 静态画面本身要能看懂 |
| Live Activity 定位是「进行中的临时事件」 | 长期常驻有审核风险，已设 staleDate |
| 第三方 App 无法设置动态壁纸 | 不用考虑这条路线 |

**结论**：所有「动起来」的体验都在主 App；小组件和灵动岛负责「瞄一眼就知道噜噜现在怎么样」。

## 未验证 / 首次编译要检查

- [ ] `xcodegen generate` 无报错，`LuluPet.xcodeproj` 生成
- [ ] 两个 target 都编译通过（Swift 代码**未经编译验证**，可能有 API 细节需要微调）
- [ ] App Group 读写正常（主 App 改数值，桌面小组件能刷新出来）
- [ ] 小组件五种尺寸都不空白、不裁切
- [ ] 灵动岛四种呈现都正常，`staleDate` 到期后活动能结束
- [ ] `UIImage(named: "frame-neutral")` 能取到图（bundle resource 已加入）
- [ ] 真机上授权 Live Activity 后能出现在锁屏
- [ ] 设置页三条数值随摸头/喂食变化

## 环境要求

- **Mac + Xcode 15+**（部署目标 iOS 17.0，兼容到 iOS 26）
- 或云 CI：`.github/workflows/ios-build.yml`（GitHub Actions `macos-latest`，出未签名 ipa）
- Windows 工作机只能写 Swift 代码，不能编译、签名或真机调试 —— 装机走 Sideloadly，见 `打包与安装指南.md`

## 参考项目（已下载到 `.research/templates/`）

- `pixel-pals/` — MIT，Swift + ActivityKit 灵动岛像素宠物
- `mobile-desktop-pet/` — 无 LICENSE，**只读**：`project.yml` / entitlements / 共享 JSON 的组织方式
- `VidiPT89/iVidigotchy` — MIT，SwiftUI + SpriteKit 的 App 内养成
