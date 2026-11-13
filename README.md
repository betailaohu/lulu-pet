# 水豚噜噜 · 手机桌宠

> 非商业、非官方同人项目 ｜ 以 MIT 开源桌宠为底座改造 ｜ Android 先行
> 启动日期：2026-11-13

一个以水豚噜噜为形象的手机桌宠。Android 侧做真正的悬浮窗桌宠，iOS 侧做「主 App + 桌面小组件 + 灵动岛」。两端共用同一套素材和同一份状态配置。

---

## 已确认的四项决策

| # | 决策 | 结论 |
| --- | --- | --- |
| 1 | iOS 形态 | 接受「主 App 完整互动 + WidgetKit 小组件 + ActivityKit 灵动岛」。**iOS 沙盒不允许全局悬浮窗**，这是平台上限，不是技术选型问题 |
| 2 | 素材现状 | **按「目前还没有素材」理解**（原话「现在每天素材」疑似输入法误选，若其实已有图包请告诉我路径，直接接进来）。因此先生成了 36 张可替换的占位立绘 |
| 3 | 商业化 | **不打算商业化** → 合规口径见下文，GPL 约束可放宽，IP 授权暂时不用提前谈 |
| 4 | 起步顺序 | **Android 先行**，先让水豚在桌面上动起来，iOS 随后 |

---

## 目录结构

```
F:\手机桌宠\
├── README.md                        ← 本文件
├── 桌宠开源模板选型与改造方案.md     ← 上轮调研报告（候选项目 / 许可证 / 架构论证）
├── android/                         ← Android 工程（已生成，未编译）
│   ├── app/src/main/assets/
│   │   ├── frames/                 36 张占位立绘
│   │   ├── character.png
│   │   ├── manifest.json          共享层副本
│   │   └── state.json
│   ├── LICENSE                     MIT 原文（保留）
│   ├── ORIGIN.md                   上游来源与改造记录
│   ├── MIGRATION.md                下一步：配置驱动改造（含可粘贴代码）
│   └── UPSTREAM_README.md / CHANGELOG.md   上游档案，保留原文
├── ios/                            ← iOS 工程骨架（Swift 全量，Mac 上 xcodegen 生成 .xcodeproj）
│   ├── project.yml
│   ├── Shared/ PetApp/ PetWidget/ PetLiveActivity/ Resources/
│   └── README.md
├── shared/                         ← 双端唯一事实源
│   ├── manifest.json               34 行为 / 36 帧 / 时段池 / 姿势缩放
│   ├── state.json                  养成数值 / 时段 / 交互 / 小组件文案
│   └── README.md
├── assets/lulu/                   ← 水豚噜噜素材包
│   ├── frame-*.png (36)           占位立绘
│   ├── character.png
│   ├── generate_placeholders.py   占位图生成
│   ├── sync_assets.py             替换正式素材后同步到 Android
│   └── README.md                  素材规格
└── .research/                     ← 调研资产
    ├── templates/                 4 份开源模板源码快照
    ├── gh_scan.py                 GitHub 项目扫描
    ├── download_templates.py      模板下载（走 codeload）
    └── setup_android.py           Android 工程生成 / 身份改造脚本
```

---

## 现在做到哪了

**已完成**

- 开源模板选型、许可证与平台能力调研（见方案报告）
- Android 工程骨架：从 `fvfpq/deepfish-desktop-pet-android`(MIT) 生成，包名 `com.lulu.pet`、应用名「水豚噜噜桌宠」、主题色改棕、版本号重置
- **清空上游全部角色素材**（授权隔离），现已换成 web 调研 + AI 生成的 36 张正式立绘
- 34 条行为台词、七段生理时钟文案全部换成水豚噜噜风格
- 行为表 / 状态表抽成 `shared/manifest.json` + `shared/state.json`，双端可共用
- 补齐上游缺失的 5 张帧（`dance` / `cheer` / `wonder` / `nap` / `jump`），修掉「某些时段桌宠变空白」的问题
- **运行时已切到配置驱动**：`PetManifest.kt` 读 `shared/manifest.json`，姿势缩放 / 多帧动作 / 待机帧全部外置，读取失败自动回退硬编码
- **养成系统已接入**：`PetState.kt` 读 `shared/state.json`，饱食度 / 心情按小时衰减，摸头与喂食涨亲密度，数值过低时插队播 `hungry` / `cry`
- **36 张立绘绘制清单 + AI 绘图提示词**：`assets/lulu/绘制清单.md`（由 `drawing_brief.json` 生成），分 P0/P1/P2 三批
- 自检脚本 `.research/verify_project.py`（121 项，含 512×512 RGBA 素材规格校验）、`.research/check_kotlin.py`、`.research/check_pet_onscreen.py`（真机屏幕校验）
- **iOS 工程骨架**：XcodeGen `project.yml` + 主 App / Widget Extension 完整 Swift 代码（状态机、小组件、灵动岛）+ Info.plist / entitlements，Mac 上 `xcodegen generate` 即可打开
- **云端编译通道**：`.github/workflows/android-build.yml`（JDK 17 + SDK 34，推送即出 debug APK）+ `android/编译验证指南.md`
- **正式立绘替换通道**：`assets/lulu/install_assets.py`（校验尺寸 / 命名 / 完整性后自动安装并同步双端）
- **AI 素材已安装**：15 张 ImageGen 生成 + 21 张语义复用，来源与授权边界见 `assets/lulu/asset_provenance.json`
- **Android 已编译出 APK**：2026-11-14 首次构建成功（`BUILD SUCCESSFUL in 1m`），产物 `dist/lulu-pet-0.1.0-debug.apk`（10.7 MB），内含 36 张帧与共享配置；编译坑与命令见 `android/编译验证指南.md`

**待办**

- [x] **实机功能验证（核心项）**：2026-11-14 在 25098PN5AC 上装包验证通过 —— 悬浮窗上屏、立绘渲染、时段睡眠帧、自主移动、单击摸头、养成数值衰减/封顶/持久化全部正常，无崩溃。记录见 `dist/实机验证记录.md`，复验脚本 `.research/check_pet_onscreen.py`
- [ ] **实机手势补测**（需手动）：拖动 / 甩动 / 绕圈 / 双击开聊天 / 通知栏三个按钮 / 息屏亮屏 / 重启自启
- [ ] **逐张重绘 21 张复用帧**（可选优化）：按 `绘制清单.md` 单独生成后 `python assets/lulu/install_assets.py <素材目录> --force`
- [x] **iOS 设置页 + 小组件数据源**：`SettingsView.swift` 展示三条数值 / 共享通道状态 / 刷新小组件 / 结束灵动岛 / 重置；`PetState.publish()` 每次变化写 App Group 并 `reloadAllTimelines()`
- [x] **iOS 包通道就绪**：`.github/workflows/ios-build.yml`（macOS runner 出未签名 ipa）+ `ios/打包与安装指南.md`（Sideloadly 重签装机），已按 iOS 26 / iPhone 17 调过部署目标与 API
- [ ] **第一次跑 iOS CI**：需要你先把仓库推到 GitHub（命令见指南），Swift 代码至今没被真编译过

---

## 怎么跑起来（Android）

本机 Windows 已经装了一套隔离工具链（`C:\Users\Administrator\.workbuddy\toolchain\`，不改系统环境变量），**可以直接出 APK**，产物在 `dist/`。要重新构建：

```bash
export JAVA_HOME="C:/Users/Administrator/.workbuddy/toolchain/jdk17"
export ANDROID_HOME="C:/Users/Administrator/.workbuddy/toolchain/android-sdk"
cd android && ./gradlew assembleDebug
```

换一台机器的话：

1. 装 **JDK 17** + **Android Studio**（SDK Platform 34，Build Tools 34）
2. 打开 `android/`，等 Gradle Sync 完成
3. `./gradlew assembleDebug`（或点 Run），生成 APK
4. 安装后授予「显示在其他应用上层」权限，点「启动桌宠」
5. 建议把应用加入电池优化白名单，避免后台被杀

完整验证清单在 `android/MIGRATION.md` 末尾，编译排错在 `android/编译验证指南.md`。

---

## 怎么拿 iOS 包

Windows 编不了 iOS，`.ipa` 必须由 macOS 产出。走 GitHub Actions 就绕开了这个限制：

1. 仓库推到 GitHub → Actions → **iOS Build** → Run workflow
2. 下载 artifact `LuluPet-unsigned-ipa`（未签名）
3. Windows 上装 **Apple Devices** + **Sideloadly**，用你的 Apple ID 重签后装进 iPhone

完整步骤、免费 Apple ID 的 7 天期限 / 3 个 App 上限 / 拿不到 App Groups 这些坑，都写在 `ios/打包与安装指南.md`。

---

## 合规口径（不商业化）

既然不打算商业化，约束可以放宽，但下面几条仍按最稳妥的方式处理：

- **MIT 义务已履行**：`android/LICENSE` 保留上游原文，未修改未删除。
- **上游角色素材已全部移除**：代码是 MIT，但角色立绘权利归原作者、不随源码授权。工程内现在是 AI 生成的风格近似原创图，不含任何网络抓取的成品图。
- **GPL 模板**：不分发 / 不商业化的场景下约束基本不触发，Dollhouse 之类现在可以自由参考甚至 fork——但 fork 后一旦发布，衍生部分仍须按 GPL-3.0 开源。**本项目仍以 MIT 的 deepfish 为底座**，纯粹是省掉这些麻烦，不给自己留坑。
- **水豚噜噜是第三方 IP**（版权方：铁罐(北京)文化传媒有限公司，源自动画《平头哥》）：非商业、非官方同人定位，风险较低，但建议：
  - web 只用于提取形象设定与气质参考，**没有下载或复制官方 / 同人成品图片**
  - AI 生成图是风格近似的原创绘制，不是官方素材；来源记录见 `assets/lulu/asset_provenance.json`
  - 明确标注「非官方同人作品」，不冒充官方、不使用官方商标做宣传
  - 不接广告、不做内购、不做任何收费
  - **若以后改主意要商业化或上架分发，先谈形象授权并改用官方素材**，别等整套素材做完才发现不能用
- **灵动岛审核**：Apple 把 Live Activity 定位为「进行中的临时事件」，常驻桌宠有被拒风险。做成有时长、有明确结束条件的活动更稳。

---

## 关键约束（别踩坑）

- iOS **不能**做全局悬浮窗、不能连续播动画、不能设动态壁纸；所有「动」的体验放主 App，小组件只做静态状态卡。
- WidgetKit 刷新由系统调度（约 15–60 分钟一次），不要按秒级动画设计；动画上限 2 秒。
- 一套素材两端通吃的前提：保持 512×512、同一锚点、同一命名 `frame-<id>.png`。

---

## 相关文档

| 想看什么 | 去哪 |
| --- | --- |
| 为什么这么选型、有哪些候选项目、许可证对比 | `桌宠开源模板选型与改造方案.md` |
| Android 下一步怎么改 | `android/MIGRATION.md` |
| 上游来源与改造清单 | `android/ORIGIN.md` |
| 双端配置字段说明 | `shared/README.md` |
| 素材规格与替换流程 | `assets/lulu/README.md` |
| iOS 三 target 怎么建、平台限制 | `ios/README.md` |
