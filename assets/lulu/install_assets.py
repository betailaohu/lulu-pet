"""安装正式立绘：校验外部素材 → 同名覆盖占位图 → 同步到 Android + iOS。

用法：
  python install_assets.py <素材目录>
  python install_assets.py <素材目录> --force     # 允许只替换部分帧（其余仍用占位图）

校验规则：
  - 文件名必须是 frame-<id>.png，且 id 在 shared/manifest.json#frameFiles 里
  - 必须是合法 PNG 且尺寸 512×512
  - character.png 可选（512×512）
  - 默认要求 36 张齐全；--force 允许分批替换

全部通过后才会覆盖 assets/lulu/ 并自动调用 sync_assets.py。
"""
import json
import os
import shutil
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SHARED = os.path.join(ROOT, "shared")

args = [a for a in sys.argv[1:] if not a.startswith("--")]
force = "--force" in sys.argv

if not args:
    raise SystemExit("用法: python install_assets.py <素材目录> [--force]")

src_dir = os.path.abspath(args[0])
if not os.path.isdir(src_dir):
    raise SystemExit("[FAIL] 目录不存在: " + src_dir)

expected = set(json.load(
    open(os.path.join(SHARED, "manifest.json"), encoding="utf-8")
)["frameFiles"])


def png_size(path):
    with open(path, "rb") as fh:
        head = fh.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


problems = []
found = {}

for name in sorted(os.listdir(src_dir)):
    if not name.startswith("frame-"):
        continue
    if not name.lower().endswith(".png"):
        problems.append("只支持 PNG: " + name)
        continue
    frame_id = name[len("frame-"):-4]
    if frame_id not in expected:
        problems.append("不在 manifest 里的帧: " + name)
        continue
    path = os.path.join(src_dir, name)
    size = png_size(path)
    if size != (512, 512):
        problems.append("尺寸不是 512x512 ({}): {}".format(size, name))
        continue
    found[frame_id] = (name, path)

missing = sorted(expected - set(found))
if missing and not force:
    problems.append("缺 {} 张帧（加 --force 可分批替换）: {}".format(
        len(missing), ", ".join(missing)
    ))

if problems:
    print("[FAIL] 校验未通过，未改动任何文件：")
    for p in problems:
        print("  -", p)
    raise SystemExit(1)

for frame_id, (name, path) in found.items():
    shutil.copy2(path, os.path.join(HERE, name))

char_src = os.path.join(src_dir, "character.png")
if os.path.isfile(char_src):
    if png_size(char_src) == (512, 512):
        shutil.copy2(char_src, os.path.join(HERE, "character.png"))
    else:
        print("[WARN] character.png 尺寸不是 512x512，已跳过")

marker = os.path.join(HERE, ".placeholder")
if os.path.isfile(marker) and not missing:
    os.remove(marker)

print("[OK] 安装 {} 张正式立绘".format(len(found)))
if missing:
    print("[WARN] 仍有 {} 张是占位图: {}".format(len(missing), ", ".join(missing)))

subprocess.run(
    [sys.executable, os.path.join(HERE, "sync_assets.py")],
    check=True
)
print("[OK] 已同步到 Android 与 iOS；建议再跑一次 python .research/verify_project.py")
