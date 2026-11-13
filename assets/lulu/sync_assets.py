"""把 assets/lulu/ 的立绘 + shared/ 的配置同步到 Android 与 iOS 工程（替换正式素材后运行一次即可）。

用法：
  python sync_assets.py
"""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = HERE
FRAMES = os.path.join(ROOT, "android", "app", "src", "main", "assets", "frames")
ASSETS = os.path.join(ROOT, "android", "app", "src", "main", "assets")

if not os.path.isdir(FRAMES):
    raise SystemExit("[FAIL] 找不到 android/app/src/main/assets/frames，请先运行 .research/setup_android.py")

for name in os.listdir(FRAMES):
    if name.lower().endswith((".png", ".webp")):
        os.remove(os.path.join(FRAMES, name))

n = 0
for name in sorted(os.listdir(SRC)):
    if name.startswith("frame-") and name.lower().endswith((".png", ".webp")):
        shutil.copy2(os.path.join(SRC, name), os.path.join(FRAMES, name))
        n += 1

for ext in (".png", ".webp"):
    p = os.path.join(SRC, "character" + ext)
    if os.path.isfile(p):
        shutil.copy2(p, os.path.join(ASSETS, "character" + ext))
        break

SHARED = os.path.join(ROOT, "shared")
for cfg in ("manifest.json", "state.json"):
    src = os.path.join(SHARED, cfg)
    if os.path.isfile(src):
        shutil.copy2(src, os.path.join(ASSETS, cfg))

IOS_RES = os.path.join(ROOT, "ios", "Resources")
ios_n = 0
if os.path.isdir(IOS_RES):
    ios_frames = os.path.join(IOS_RES, "Frames")
    os.makedirs(ios_frames, exist_ok=True)
    for name in os.listdir(ios_frames):
        if name.lower().endswith((".png", ".webp")):
            os.remove(os.path.join(ios_frames, name))
    for name in sorted(os.listdir(SRC)):
        if name.startswith("frame-") and name.lower().endswith((".png", ".webp")):
            shutil.copy2(os.path.join(SRC, name), os.path.join(ios_frames, name))
            ios_n += 1
    for cfg in ("manifest.json", "state.json"):
        src = os.path.join(SHARED, cfg)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(IOS_RES, cfg))

WEB = os.path.join(ROOT, "web")
web_n = 0
if os.path.isdir(WEB):
    web_assets = os.path.join(WEB, "assets")
    web_frames = os.path.join(web_assets, "frames")
    os.makedirs(web_frames, exist_ok=True)
    for name in os.listdir(web_frames):
        if name.lower().endswith((".png", ".webp")):
            os.remove(os.path.join(web_frames, name))
    for name in sorted(os.listdir(SRC)):
        if name.startswith("frame-") and name.lower().endswith((".png", ".webp")):
            shutil.copy2(os.path.join(SRC, name), os.path.join(web_frames, name))
            web_n += 1
    for cfg in ("manifest.json", "state.json"):
        src = os.path.join(SHARED, cfg)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(web_assets, cfg))

print("synced {} frames + character.* + shared/*.json -> {}".format(n, ASSETS))
if ios_n:
    print("synced {} frames + shared/*.json -> {}".format(ios_n, IOS_RES))
if web_n:
    print("synced {} frames + shared/*.json -> {}".format(web_n, WEB))
