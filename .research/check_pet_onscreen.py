"""实机验证：确认桌宠窗口是否真的画在屏幕上（不依赖肉眼看截图）。

做三件事：
1. 从 dumpsys window 读出 com.lulu.pet 的窗口可见性 / 绘制状态 / 屏幕矩形
2. 抓一张截图，统计窗口矩形内的暖色与深色像素占比，并与同尺寸对照区对比
3. 连拍两帧比对，确认立绘在动（不是卡死）

用法：
  python .research/check_pet_onscreen.py [serial]
"""
import os
import re
import subprocess
import sys
import time

ADB = r"C:\Users\Administrator\.workbuddy\toolchain\android-sdk\platform-tools\adb.exe"
DISPLAY_ID = "4630946949513469331"  # 主屏，dumpsys SurfaceFlinger --display-id 可查
LOCAL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dist")
SERIAL = sys.argv[1] if len(sys.argv) > 1 else "4734fc75"


def sh(*args, binary=False):
    cmd = [ADB, "-s", SERIAL] + list(args)
    r = subprocess.run(cmd, capture_output=True)
    return r.stdout if binary else r.stdout.decode("utf-8", "ignore")


def window_info():
    dump = sh("shell", "dumpsys", "window", "windows")
    block = ""
    for i, line in enumerate(dump.splitlines()):
        if "Window #" in line and "com.lulu.pet}" in line:
            block = "\n".join(dump.splitlines()[i:i + 40])
            break
    info = {
        "found": bool(block),
        "visible": "isVisible=true" in block,
        "has_surface": "mHasSurface=true" in block,
        "drawn": "HAS_DRAWN" in block,
        "on_screen": "isOnScreen=true" in block,
    }
    m = re.search(r"frame=\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]", block)
    info["rect"] = tuple(int(v) for v in m.groups()) if m else None
    return info


def grab(name):
    remote = "/sdcard/%s.png" % name
    local = os.path.join(LOCAL, "_%s.png" % name)
    sh("shell", "screencap", "-d", DISPLAY_ID, "-p", remote)
    sh("pull", remote, local)
    return local


def stats(path, box, label):
    from PIL import Image
    im = Image.open(path).convert("RGB")
    px = im.load()
    w, h = im.size
    x0, y0, x1, y1 = box
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(w - 1, x1), min(h - 1, y1)
    warm = dark = n = 0
    for y in range(y0, y1, 2):
        for x in range(x0, x1, 2):
            r, g, b = px[x, y]
            n += 1
            if r > 170 and 95 < g < 220 and b < 165 and r - b > 45:
                warm += 1
            if (r + g + b) / 3 < 80:
                dark += 1
    print("  %-14s %4dx%-4d 暖色 %5.1f%%  深色 %5.1f%%" % (
        label, x1 - x0, y1 - y0, 100.0 * warm / max(n, 1), 100.0 * dark / max(n, 1)))
    return 100.0 * warm / max(n, 1)


def diff_bbox(p1, p2):
    from PIL import Image
    a = Image.open(p1).convert("RGB")
    b = Image.open(p2).convert("RGB")
    pa, pb = a.load(), b.load()
    w, h = a.size
    minx, miny, maxx, maxy, n = w, h, 0, 0, 0
    for y in range(0, h, 3):
        for x in range(0, w, 3):
            p, q = pa[x, y], pb[x, y]
            if abs(p[0] - q[0]) + abs(p[1] - q[1]) + abs(p[2] - q[2]) > 45:
                n += 1
                minx, maxx = min(minx, x), max(maxx, x)
                miny, maxy = min(miny, y), max(maxy, y)
    return n, (minx, miny, maxx, maxy) if n else None


def main():
    os.makedirs(LOCAL, exist_ok=True)
    print("[1] 窗口状态")
    info = window_info()
    for k, v in info.items():
        print("  %-11s %s" % (k, v))
    if not info["found"]:
        print("  [FAIL] 没找到桌宠悬浮窗 —— 服务没启动或权限没给")
        return 1

    print("[2] 截图采样")
    p1 = grab("onscreen1")
    x0, y0, x1, y1 = info["rect"] or (0, 0, 350, 600)
    pet = stats(p1, (x0, y0, x1, y1), "桌宠窗口")
    ctrl = stats(p1, (max(0, x0 - 400), y0, max(0, x1 - 400), y1), "左侧对照")
    print("  差值 %.1f 个百分点（>8 说明窗口区域有自己的内容）" % (pet - ctrl))

    print("[3] 连拍比对（1.2s）")
    time.sleep(1.2)
    p2 = grab("onscreen2")
    n, box = diff_bbox(p1, p2)
    print("  变化采样点 %d  bbox %s" % (n, box))
    if box:
        cx, cy = (box[0] + box[2]) // 2, (box[1] + box[3]) // 2
        inside = x0 <= cx <= x1 and y0 <= cy <= y1
        print("  变化中心 (%d,%d) 是否落在桌宠窗口内: %s" % (cx, cy, inside))

    ok = info["visible"] and info["has_surface"] and info["drawn"] and info["on_screen"] and pet > ctrl + 5
    print("\n=== %s ===" % ("通过：桌宠确实画在屏幕上" if ok else "存疑：窗口存在但按像素看不像有立绘"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
