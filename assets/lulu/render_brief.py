"""从 drawing_brief.json 生成人读的《绘制清单.md》，保证两份内容永远一致。

用法：python render_brief.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "drawing_brief.json")
OUT = os.path.join(HERE, "绘制清单.md")

with open(SRC, encoding="utf-8") as fh:
    data = json.load(fh)

spec = data["spec"]
frames = data["frames"]
L = []

L.append("# 水豚噜噜 · 36 张立绘绘制清单\n")
L.append("> 由 `drawing_brief.json` 生成，改数据后重跑 `python render_brief.py`。\n")
L.append("> " + data["note"] + "\n")

L.append("\n## 规格\n")
L.append("| 项 | 值 |\n| --- | --- |")
L.append("| 画布 | {} × {} px |".format(*spec["canvas"]))
L.append("| 锚点 | ({}, {})，脚底中心，所有帧对齐 |".format(*spec["anchor"]))
L.append("| 格式 | {} |".format(spec["format"]))
L.append("| 命名 | `{}`，大小写敏感 |".format(spec["naming"]))
L.append("| 数量 | {} 张 |\n".format(spec["count"]))

L.append("\n## 怎么用这份清单\n")
L.append("每张图的完整提示词 = **stylePrefix** + `, ` + 该行的 **prompt 片段**，`negativePrompt` 单独作为负向提示词。\n")
L.append("**所有 36 张必须使用完全相同的 stylePrefix**，否则切换状态时会跳戏。\n")
L.append("```text\nSTYLE PREFIX:\n{}\n```\n".format(data["stylePrefix"]))
L.append("```text\nNEGATIVE PROMPT:\n{}\n```\n".format(data["negativePrompt"]))
L.append("```text\n{}\n```\n".format(data["promptRule"]))

status = data.get("assetStatus")
if status:
    L.append("\n## 素材现状\n")
    L.append("| 项 | 值 |\n| --- | --- |")
    L.append("| AI 生成核心帧 | {} 张 |".format(status["aiGenerated"]))
    L.append("| 语义复用补齐 | {} 张 |".format(status["reused"]))
    L.append("| 已安装到工程 | {} |".format("是" if status["installed"] else "否"))
    L.append("| 来源记录 | `{}` |".format(status["provenance"]))
    L.append("| 工作流 | {} |\n".format(status["workflow"]))
    L.append("> 复用的帧是复制语义最接近的 AI 帧，**不是独立绘制**；后续可逐张单独重绘后按同名覆盖，不需要改任何代码。\n")

L.append("\n## 分三批画\n")
for key, desc in data["priority"].items():
    count = sum(1 for f in frames if f["priority"] == key)
    L.append("- **{}**（{} 张）：{}".format(key, count, desc))

for key in data["priority"]:
    group = [f for f in frames if f["priority"] == key]
    L.append("\n### {} · {} 张\n".format(key, len(group)))
    L.append("| frameId | 对应行为 | 画面（姿势 / 表情 / 元素） | prompt 片段 |")
    L.append("| --- | --- | --- | --- |")
    for f in group:
        scene = "{}；{}；{}".format(f["pose"], f["expression"], f["prop"])
        L.append("| `{}` | {} | {} | `{}` |".format(
            f["id"], " / ".join(f["behaviors"]), scene, f["prompt"]
        ))

L.append("\n## 交付流程\n")
L.append("1. 按 `frame-<id>.png` 同名输出，覆盖 `assets/lulu/` 里的占位图（占位图带斜线纹理，一眼可辨）。")
L.append("2. 运行 `python assets/lulu/sync_assets.py` 同步进 Android 工程（图片 + `shared/*.json` 一起同步）。")
L.append("3. 若角色轮廓变化较大，调整 `shared/manifest.json#poseScale` 的缩放系数。")

L.append("\n## 一致性检查（画完逐项过）\n")
L.append("- [ ] 36 个文件齐了，文件名与 `shared/manifest.json#frameFiles` 完全一致")
L.append("- [ ] 全部 512×512、透明底、脚底中心对齐 (256, 480)")
L.append("- [ ] 线条粗细、配色、角色比例在所有帧里一致")
L.append("- [ ] `neutral` 与 `blink` 除眼睛外像素级相同（否则眨眼会跳）")
L.append("- [ ] `walk` 与 `walk-b` 是同一视角的镜像迈步帧")
L.append("- [ ] 没有任何文字、水印、Logo、投影到背景上")
L.append("- [ ] 换正式素材后，Android 端所有时段行为都不再显示空白")

with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("\n".join(L) + "\n")

print("generated {} ({} frames, {} bytes)".format(OUT, len(frames), os.path.getsize(OUT)))
