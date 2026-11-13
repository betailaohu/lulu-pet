# 共享层（双端唯一事实源）

这个目录放**与平台无关**的配置。Android 和 iOS 都读同一份，避免两套逻辑各自漂移。

| 文件 | 职责 |
| --- | --- |
| `manifest.json` | 表现层：素材规格、36 个 frameId、34 个行为（帧 / 时长 / 台词 / 表情）、别名、时段行为池、多帧动作、姿势缩放 |
| `state.json` | 状态层：七段生理时钟、养成数值、空闲节奏、交互映射、状态文案、小组件 / 灵动岛布局 |

## 字段速查

**manifest.json**

- `assetSpec` — 画布 / 锚点 / 命名规则 / 是否占位素材
- `frameFiles` — 所有合法 frameId（36 个）
- `frameAliases` — `dream→sleep`、`dizzy→shock`、`jump→fly`
- `behaviors.<id>` — `scene` / `expression` / `icon` / `duration`(ms) / `line` / `frame` / 可选 `trigger` / `multiFrame`
- `scenePlans.<phaseId>` — 该时段随机抽取的行为池
- `multiFrameActions` — 少数走多帧循环的动作（`ciallo` / `dance`）及帧间隔
- `restingFrame` — 默认待机帧与睡眠时段待机帧
- `poseScale` — `groups` 数组按缩放值分组（精确对应上游 `poseVisualScale()`），`default` 兜底；换素材后按实际轮廓重调

**state.json**

- `bodyClock` — 7 段时段（`from` / `to` 为小时），`id` 对应 `scenePlans` 的 key
- `stats` — 饱食度 / 心情 / 亲密度，含衰减与阈值
- `idle` — 空闲行为间隔
- `interactions` — 点击 / 双击 / 拖动 / 绕圈 / 亮屏息屏的映射
- `statusText` — 供小组件显示的状态文案（带 condition）
- `widget` / `liveActivity` — iOS 侧布局与 App Group id、平台限制备注

## 双端如何消费

**Android（已接入）**

`shared/*.json` 的副本在 `android/app/src/main/assets/`，由 `assets/lulu/sync_assets.py` 同步。运行时由 `PetManifest.kt` 读 `manifest.json`、`PetState.kt` 读 `state.json`，两者都在 `PetService.onCreate()` 初始化；配置读取失败会自动回退到硬编码兜底。改造记录与回滚参考见 `android/MIGRATION.md`。

**iOS**

把两份 JSON 加入 Xcode 的 Copy Bundle Resources，用 `Codable` 解析：

```swift
struct Manifest: Codable {
    let frameFiles: [String]
    let frameAliases: [String: String]
    let behaviors: [String: Behavior]
    let scenePlans: [String: [String]]
}

struct Behavior: Codable {
    let frame: String
    let duration: Int
    let line: String
    let expression: String
}
```

- **主 App**：读 `behaviors` + `scenePlans` 做状态立绘切换（`UIImage(named: "frame-\(id)")`）与位移。
- **小组件**：读 `state.json#widget`，取 `neutral` 静态图 + `statusText`；数据通过 App Group `group.com.lulu.pet` 的 `UserDefaults` 从主 App 传入。
- **灵动岛**：读 `state.json#liveActivity`。
- 素材需同时加进 Xcode Asset Catalog 或 bundle，文件名保持一致。

## 修改流程

1. 只改 `shared/` 下的 JSON，**不要直接改 Android assets 里的副本**。
2. 重新同步：`python assets/lulu/sync_assets.py` 只同步图片；JSON 用 `cp shared/*.json android/app/src/main/assets/`，或重建工程（`.research/setup_android.py`）。
3. 改完用 `python -m json.tool shared/manifest.json` 校验格式。
4. 双端各自跑一遍验证清单（`android/MIGRATION.md` 末尾有 Android 版）。
