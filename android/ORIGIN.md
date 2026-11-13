# 上游来源与改造记录

## 上游

- **项目**：[fvfpq/deepfish-desktop-pet-android](https://github.com/fvfpq/deepfish-desktop-pet-android)（v1.2.6）
- **协议**：MIT，`android/LICENSE` 为上游原文，**未修改、未删除**（MIT 要求保留版权与许可声明）
- **上游档案**：`UPSTREAM_README.md`、`CHANGELOG.md` 保留原文未改动，因此里面仍有「蓝色大肥鱼」「deepfish」等旧称，属正常，不代表本项目身份。

## 已完成的改造

| 项 | 上游 | 本项目 |
| --- | --- | --- |
| 包名 / applicationId | `com.deepfish.pet` | `com.lulu.pet` |
| 工程名 | `DeepFishPet` | `LuluPet` |
| 应用名 | 蓝色大肥鱼桌宠 | 水豚噜噜桌宠 |
| 主题 | `Theme.DeepFish` / `fish_blue #2E8BEF` | `Theme.Lulu` / `lulu_brown #B98A62` |
| 常量前缀 | `deepfish_*` | `lulu_*`（SharedPreferences、通知渠道、KeyStore 别名、Action 常量） |
| 角色素材 | 31 张上游角色立绘 + `character.png` | **已全部删除**，改为 36 张程序生成的水豚噜噜占位立绘 |
| 行为台词 | 原角色梗（大肥鱼 / AGI 训练 / 竞品模型） | 34 条水豚噜噜佛系文案 |
| 生理时钟文案 | 原角色设定 | 水豚噜噜七段时段文案 |
| 版本 | versionCode 14 / 1.2.6 | versionCode 1 / 0.1.0 |
| 共享配置 | 无 | `app/src/main/assets/` 下已放 `manifest.json` + `state.json` |

改造由 `.research/setup_android.py` 脚本完成，可审计、可重放（脚本幂等，`android/` 已存在时会跳过）。

## 授权边界

- **代码**：MIT，可闭源、可商用，只需保留 `LICENSE`。
- **上游角色素材**：权利归原作者，**不随源码授权**，已从工程内全部移除。工程内现有的 36 张立绘是本项目自己用脚本生成的占位图，与上游形象无关。
- **水豚噜噜**：第三方 IP。本项目定位为**非商业、非官方同人**，见根目录 `README.md` 的合规说明。

## 第三轮：配置驱动与养成系统（同日）

| 项 | 内容 |
| --- | --- |
| 表现层配置化 | 新增 `model/PetManifest.kt`，读 `assets/manifest.json`；`PetView` 的 `get` / `getPlan` / `frameName` / `poseScale` / `multiFrameAction` / `restingFrame` 全部改为走配置，`Behaviors.kt` 只留 data class、文本处理与兜底表 |
| 兜底策略 | JSON 读取失败时 `PetManifest` 自动回退硬编码表，桌宠不会空白或崩溃 |
| 养成数值 | 新增 `PetState.kt`，读 `state.json#stats`；SharedPreferences 持久化、按小时衰减、摸头/喂食增长与每日上限、低阈值插队行为、`statusText()` / `snapshot()` 出口 |
| 交互调整 | 单击由「随机说句话」改为「摸头 → `PetState.onPat()` + 播 `pat`」；新增 `onCommand("feed")` |
| 静态自检 | `.research/verify_project.py`（73 项全过）、`.research/check_kotlin.py`（14 个 Kotlin 文件括号平衡） |

## 第四轮：iOS 工程 / 云端编译 / 素材替换通道（同日）

| 项 | 内容 |
| --- | --- |
| iOS 工程骨架 | `ios/project.yml`（XcodeGen，**2 个 target**：PetApp + PetWidget；Live Activity 属于 Widget Extension）+ 完整 Swift 代码（AppGroup / PetManifest / PetState / PetView / Widget / Live Activity）+ Info.plist / entitlements |
| 双端素材同步 | `sync_assets.py` 扩展为同时同步 `ios/Resources/Frames/` 与两份 JSON；`ios/Resources/` 已有 36 张帧和配置 |
| 云端编译 | `.github/workflows/android-build.yml`（JDK 17 + SDK 34 → `assembleDebug` → 上传 APK），绕过本机无构建环境 |
| 编译指南 | `android/编译验证指南.md`（三条路径 + 常见失败排查 + 功能验证清单） |
| 正式素材安装 | `assets/lulu/install_assets.py`（校验尺寸/命名/完整性 → 覆盖 → 自动同步双端 → 清除 `.placeholder` 标记） |
| 文档修正 | 早先「三个 target」的说法改为正确的「2 个 target」；本文件「未改动运行时逻辑」的说法已过时，见第三轮 |

## 第五轮：web 形象调研 + AI 生成正式立绘（2026-11-14）

| 项 | 内容 |
| --- | --- |
| web 调研 | 确认水豚噜噜（Capylulu）为**铁罐(北京)文化传媒有限公司**原创 IP，源自《平头哥》少年篇；形象特征：圆滚滚奶黄身体、头顶带绿叶橘子、大而黑的眼睛、短四肢、标志性漏齿笑、佛系淡定。**只提取设定，未下载任何成品图** |
| AI 生成 | ImageGen 生成 15 张 P0 核心帧（统一 stylePrefix + 逐帧姿势）；`background=transparent` 实测输出仍是 RGB 白底，改由 `process_ai_assets.py` flood-fill 抠图 |
| 后处理 | 缩放到 512×512 RGBA、脚底对齐 (256,480)、边缘羽化；产物在 `ai_processed/` |
| 补齐 | `fill_remaining.py` 按语义复用补齐 21 张，`asset_provenance.json` 记录每帧来源与版权边界 |
| 安装 | `install_assets.py` 校验 36 张规格 → 覆盖占位图 → 同步 Android + iOS → 删除 `.placeholder` |
| 配置同步 | `drawing_brief.json#stylePrefix` 换成调研得到的准确设定；`绘制清单.md` 重生成并新增「素材现状」段 |
| 合规 | 非商业、非官方同人；AI 图为风格近似原创，不是官方素材；若商业化须先取得版权方授权并改用官方素材 |

## 第六轮：本机首次编译成功，出 APK（2026-11-14）

| 项 | 内容 |
| --- | --- |
| 工具链 | 本机临时装独立工具链（不改系统环境变量）：JDK 17（清华 Adoptium 镜像）、Android SDK platform-34 + build-tools 34.0.0 + platform-tools（腾讯云 AndroidSDK 镜像）、Gradle 8.9（腾讯云 gradle 镜像），均在 `C:\Users\Administrator\.workbuddy\toolchain\` |
| 修复 1 | **项目路径含中文**导致 AGP 直接拒绝构建 → `gradle.properties` 加 `android.overridePathCheck=true` |
| 修复 2 | **`maven.google.com` 不可达**导致依赖下载卡住 → `settings.gradle.kts` 前置阿里云镜像（google / central / gradle-plugin），官方仓库保底 |
| 修复 3 | **上游工程没有 Gradle wrapper**（`gradlew` 不存在，`./gradlew assembleDebug` 与 CI 都跑不通）→ 用 Gradle 8.9 生成 `gradlew` / `gradlew.bat` / `gradle/wrapper/*` |
| 结果 | `BUILD SUCCESSFUL in 1m`，35 个 task 全执行，仅 warning 无 error；APK 10.7 MB，内含 36 张帧 + `manifest.json` + `state.json` + `classes.dex` |
| 产物 | `dist/lulu-pet-0.1.0-debug.apk` |

## 未验证项

- **Android**：编译已通过，**但未实机验证功能**（悬浮窗权限、单击 `pat`、拖动/绕圈、时段切换、`PetManifest.isLoaded`）。清单见 `android/编译验证指南.md` 末尾。
- **iOS**：Mac 上 `cd ios && xcodegen generate`；Swift 代码与 Android 一样没有编译过，可能有 API 细节需要按 Xcode 报错微调。
