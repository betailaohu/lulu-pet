# 改造路线：从「硬编码」到「共享配置驱动」

## 当前状态（步骤 1–4 已全部接入）

- ✅ `PetManifest.kt` 已落地，由 `PetService.onCreate()` 初始化；`PetView` 的行为查询、帧别名、时段池、姿势缩放、多帧动作、待机帧**全部读 `shared/manifest.json`**。
- ✅ `Behaviors.kt` 现在只保留 `Behavior` data class、`formatLine()`、`stripHints()` 和一张兜底表；配置读取失败时自动回退，桌宠不会空白或崩溃。
- ✅ `PetState.kt` 已接入养成数值（饱食度 / 心情 / 亲密度），见下文「养成系统」。
- ✅ 静态自检：`python .research/verify_project.py` → **73 项全过**；`python .research/check_kotlin.py` → 14 个 Kotlin 文件括号平衡、无残留引用。
- ⚠️ **仍未编译验证**：本机没有 JDK / Android SDK。首次在 Android Studio 里 Sync 之后请跑一遍末尾的验证清单。

下面的步骤 1–5 现在作为**改造记录 / 回滚参考**保留，不需要再执行。其中步骤 1 的代码块是最初的接入草稿，最终实现已扩展（`poseScale` / `multiFrameAction` / `restingFrame` / `hasFrame`），**不要用它覆盖现有的 `PetManifest.kt`**。

---

## 步骤 1 · 新增 `model/PetManifest.kt`

放到 `app/src/main/java/com/lulu/pet/model/PetManifest.kt`。用 Android 内置的 `org.json`，不需要加依赖。

```kotlin
package com.lulu.pet.model

import android.content.Context
import org.json.JSONObject

object PetManifest {

    private var behaviors: Map<String, Behavior> = emptyMap()
    private var plans: Map<String, List<String>> = emptyMap()
    private var aliases: Map<String, String> = emptyMap()
    private var loaded = false

    val isLoaded: Boolean get() = loaded

    fun init(context: Context) {
        runCatching {
            val root = JSONObject(
                context.assets.open("manifest.json").bufferedReader().use { it.readText() }
            )

            val bObj = root.getJSONObject("behaviors")
            val bMap = mutableMapOf<String, Behavior>()
            for (id in bObj.keys()) {
                val o = bObj.getJSONObject(id)
                bMap[id] = Behavior(
                    id = id,
                    scene = o.optString("scene"),
                    expression = o.optString("expression"),
                    icon = o.optString("icon"),
                    duration = o.optLong("duration"),
                    line = o.optString("line")
                )
            }

            val pObj = root.getJSONObject("scenePlans")
            val pMap = mutableMapOf<String, List<String>>()
            for (k in pObj.keys()) {
                val arr = pObj.getJSONArray(k)
                pMap[k] = (0 until arr.length()).map { arr.getString(it) }
            }

            val aObj = root.optJSONObject("frameAliases")
            val aMap = mutableMapOf<String, String>()
            if (aObj != null) {
                for (k in aObj.keys()) aMap[k] = aObj.getString(k)
            }

            behaviors = bMap
            plans = pMap
            aliases = aMap
            loaded = true
        }
    }

    private fun table(): Map<String, Behavior> =
        if (loaded) behaviors else Behaviors.behaviors

    fun get(id: String): Behavior {
        val src = table()
        return src[id] ?: src.getValue("think")
    }

    fun getPlan(phaseId: String): List<String> {
        val src = if (loaded) plans else Behaviors.scenePlans
        return (src[phaseId] ?: src.getValue("default")).toList()
    }

    fun frameName(name: String): String =
        (if (loaded) aliases[name] else null) ?: Behaviors.frameName(name)
}
```

`loaded = false` 时自动回退到硬编码表，所以就算 JSON 读失败也不会崩，桌宠照常显示。

## 步骤 2 · 初始化

`PetService.onCreate()` 的第一行加：

```kotlin
PetManifest.init(this)
```

（`PetView` 是在 Service 里创建的，所以这行一定早于任何一次 `setFrame()`。）

## 步骤 3 · 切换调用点

`PetView.kt` 里只有 6 处引用 `Behaviors`，把其中 3 类换成 `PetManifest`：

| 原调用 | 改为 |
| --- | --- |
| `Behaviors.frameName(name)` | `PetManifest.frameName(name)` |
| `Behaviors.get(id)` | `PetManifest.get(id)` |
| `Behaviors.getPlan(phase.id)` | `PetManifest.getPlan(phase.id)` |

`Behaviors.formatLine(...)` 和 `Behaviors.stripHints(...)` 是纯文本处理，**保持不变**。

## 步骤 4 · 姿势缩放也读配置

`PetView.kt` 的 `poseVisualScale(frame: String)` 现在是一大段 `when`，系数写死在代码里。改成读 `manifest.json#poseScale`（`curious` 单值 + `small` / `medium` / `large` 三组 id 列表 + `default`）。换正式素材后只需改 JSON，不用再动 Kotlin。

## 步骤 5 · 清理

确认 `PetManifest.isLoaded == true` 且桌宠所有动作正常后，把 `Behaviors.kt` 里那张 34 行的 `behaviors` 表和 `scenePlans` 删掉，只留 `Behavior` data class、`formatLine()`、`stripHints()` 作为兜底。此时 `shared/manifest.json` 成为唯一事实源。

---

## 养成系统（PetState，已接入）

`PetState.kt` 读 `shared/state.json#stats`，数值存在 `SharedPreferences("lulu_state")`，按真实时间衰减：

| 数值 | 初值 | 衰减 | 低阈值 | 低时行为 |
| --- | --- | --- | --- | --- |
| 饱食度 | 70 | 6 / 小时 | 30 | `hungry` |
| 心情 | 75 | 3 / 小时 | 25 | `cry` |
| 亲密度 | 10 | 不衰减 | — | 摸头 +1、喂食 +3，每日上限 20 |

接入点：

- `PetService.onCreate()` → `PetState.init(this)`
- 单击桌宠 → `PetState.onPat()` + 播放 `pat`（不再随机说一句台词）
- `onCommand("feed")` → `PetState.onFeed()` + 播放 `feed`
- 空闲调度 `nextIdleBehavior()` → 数值过低时以 40% 概率插队 `hungry` / `cry`
- `statusText()` 读 `state.json#statusText`；`snapshot()` 是留给小组件 / 设置页的数据出口

## 之后可以做的事（按优先级）

1. **把 `PetState.snapshot()` 接到小组件数据源**：Android 侧写 JSON、iOS 侧写 App Group，格式对齐 `state.json#widget`。
2. **设置页展示数值**：三条进度条 + 一个「喂食」按钮触发 `onCommand("feed")`。
3. **动态壁纸形态**：新增 `WallpaperService`，复用同一套 `setFrame()` 逻辑。
4. **省电分档**：参考 Dollhouse，交互期 16ms、贴边 250ms、熄屏 1s 心跳。
5. **清理兜底表**：确认 `PetManifest.isLoaded == true` 且长期稳定后，可删掉 `Behaviors.kt` 里那张硬编码表。

## 验证清单（首次构建后逐项过）

- [ ] `./gradlew assembleDebug` 通过
- [ ] 悬浮窗权限授予后，桌宠出现在桌面上且**不是空白**（36 张帧都存在）
- [ ] 单击 → `pat`、双击 → 聊天、拖动 → 移动、绕圈 → `dizzy`
- [ ] 锁屏/解锁 → `stretch`；深夜时段 → `sleep` 待机帧
- [ ] 通知渠道名、设置页标题、应用名都显示「水豚噜噜」
- [ ] `PetManifest.isLoaded == true`（可临时打 Log 确认）
- [ ] 单击桌宠播 `pat`，`PetState.snapshot()` 里亲密度 +1
- [ ] 触发 `feed` 后饱食度上升并播放 `feed`
- [ ] 数值掉到阈值以下后，空闲行为里开始出现 `hungry` / `cry`
