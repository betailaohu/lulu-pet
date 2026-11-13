# 水豚噜噜素材包

## 当前素材：web 调研 + AI 生成（已安装）

36 张 `frame-*.png` + `character.png` 已全部替换并同步到 Android / iOS 工程，`.placeholder` 标记已删除。

- **15 张核心帧**由 AI（ImageGen）生成，形象设定来自 web 公开资料调研；
- **21 张**按语义复用最接近的 AI 帧（不是独立绘制，逐张映射见 `asset_provenance.json`）；
- 全部经 `process_ai_assets.py` 抠白底、缩放到 512×512 RGBA、脚底对齐 (256,480)。

**这些是风格近似的原创 AI 绘制，不是官方素材，也没有复制任何网络成品图。** 完整来源、版权方与授权边界见 `asset_provenance.json`。

历史占位图由 `generate_placeholders.py` 生成；若需回退，重跑该脚本再 `sync_assets.py` 同步即可。

## 规格（替换时请保持一致）

| 项 | 值 |
| --- | --- |
| 画布 | 512 × 512 px |
| 格式 | RGBA PNG（或 WebP），透明底 |
| 锚点 | (256, 480)，脚底中心；所有帧对齐同一锚点 |
| 命名 | `frame-<frameId>.png`，**大小写敏感**（`goAway`、`ciallo-b`、`walk-b`） |
| 数量 | 36 个 frameId，见 `shared/manifest.json#frameFiles` |
| 表现方式 | **每个 frameId 一张静态立绘**，不是逐帧序列动画；动感由 `duration` 定时切换 + 程序化位移 / 缩放 / 粒子补 |
| 主立绘 | `character.png`，用于设置页 / 小组件默认图 |

为什么是「一状态一张图」而不是序列帧：上游模板就是这么做的，改造成本最低，而且**静态立绘正好能直接用于 iOS 桌面小组件**（WidgetKit 不支持连续动画）。一套素材两端通吃。

## 帧清单

| 分组 | frameId |
| --- | --- |
| 基础 / 待机 | `neutral`、`blink`、`sit`、`walk`、`walk-b` |
| 情绪 | `happy` 系：`toy`、`feed`、`cheer`、`dance`、`fly`、`jump`、`ciallo-b`；`smug` 系：`smug`、`price`、`goAway`、`ciallo` |
| 负面 | `angry`、`rival`、`panic`、`pressure`、`shock`、`startle`、`trip`、`cry`、`stranded`、`dizzy`(→`shock`) |
| 日常 | `work`、`coffee`、`wash`、`think`、`wonder`、`hungry`、`pat`、`shy` |
| 睡眠 | `sleep`、`nap`、`dream`(→`sleep`)、`stretch` |

> 原上游模板缺 `dance` / `cheer` / `wonder` / `nap` / `jump` 这几张帧，但时段行为池会调用它们，运行时会显示空白。本项目补齐了这 5 张，这是个实质修复。
>
> `dream` → `sleep`、`dizzy` → `shock`、`jump` → `fly` 是别名映射，见 `shared/manifest.json#frameAliases`。

## 绘制清单与提示词

**`绘制清单.md`** 逐张给出了 36 个 frameId 的姿势、表情、附加元素和可直接用于 AI 绘图的英文提示词片段，并附统一的 `stylePrefix` / `negativePrompt` 与分三批（P0 15 张 / P1 15 张 / P2 6 张）的优先级。

数据源是 `drawing_brief.json`，改数据后重跑：

```
python assets/lulu/render_brief.py
```

提示词描述的是**通用卡通水豚气质**，不是对第三方 IP 的复刻；正式形象请以你手上的设定或自己的设计为准。

## 替换正式素材的流程

**一条命令搞定**（会先校验，通过后才覆盖）：

```
python assets/lulu/install_assets.py <你的素材目录>
```

脚本会检查：文件名必须是 `frame-<id>.png` 且 id 在 `shared/manifest.json#frameFiles` 里、必须是合法 PNG、必须 512×512、36 张齐全。全部通过后才同名覆盖占位图，并自动调用 `sync_assets.py` 把素材和 `shared/*.json` 一起同步到 **Android + iOS** 两端，同时删掉 `.placeholder` 标记。

分批画时用 `--force` 允许只替换一部分（其余仍是占位图）：

```
python assets/lulu/install_assets.py <素材目录> --force
```

替换后：

1. 若角色轮廓变化较大，调整 `shared/manifest.json#poseScale` 的缩放系数。
2. 台词 / 时长 / 时段行为池改 `shared/manifest.json#behaviors` 与 `#scenePlans`。
3. 只改配置不换图时，直接跑 `python assets/lulu/sync_assets.py`。
4. 最后跑一次 `python .research/verify_project.py` 确认双端副本一致。

（`shared/` 是唯一事实源，不要直接改 `android/app/src/main/assets/` 或 `ios/Resources/` 里的副本。）

## 重画建议

- 保持「松弛、佛系、慢吞吞」的气质，动作幅度小，靠表情和细微姿势区分状态。
- 所有帧用同一套线条粗细和配色，避免切换时跳戏。
- 先画 10–15 个高频状态（`neutral` / `blink` / `walk` / `sleep` / `pat` / `hungry` / `think` / `happy` / `shy` / `startle`）跑通，其余用别名或复用帧顶着，再慢慢补齐。
- 如果以后确实需要骨骼动画（Live2D），这是另一条技术路线，见根目录方案报告第 3.5 节。
