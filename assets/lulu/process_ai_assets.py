"""AI 生成图后处理：抠掉白色背景 → 统一锚点对齐 → 输出 512×512 RGBA 立绘。

ImageGen 的 background=transparent 实测输出仍是 RGB 白底，所以必须在这里做抠图。

用法（需要用装了 Pillow 的隔离环境）：
  python process_ai_assets.py <源PNG> <frameId>
  python process_ai_assets.py --batch <frameId1,frameId2,...>
                              # 按 ai_generated/ 里的时间戳顺序一一对应

输出：ai_processed/frame-<id>.png
"""
import glob
import os
import sys
from collections import deque

from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "ai_generated")
OUT = os.path.join(HERE, "ai_processed")

CANVAS = 512
ANCHOR_Y = 480
TARGET_H = 400
MAX_W = 440


def is_background(rgb):
    """近白、低饱和的像素当作背景；水豚的奶黄色 min 通道明显更低，不会被误删。"""
    r, g, b = rgb[:3]
    return min(r, g, b) > 200 and (max(r, g, b) - min(r, g, b)) < 42


def remove_background(im):
    """从四边做 flood fill，只删与边界连通的背景，保留角色内部白色（牙齿等）。"""
    w, h = im.size
    rgba = im.convert("RGBA")
    px = rgba.load()
    visited = bytearray(w * h)
    queue = deque()
    seeds = [
        (0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1),
        (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2),
    ]
    for x, y in seeds:
        idx = y * w + x
        if not visited[idx] and is_background(px[x, y]):
            visited[idx] = 1
            queue.append((x, y))
    while queue:
        x, y = queue.popleft()
        r, g, b, _ = px[x, y]
        px[x, y] = (r, g, b, 0)
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < w and 0 <= ny < h:
                i2 = ny * w + nx
                if not visited[i2] and is_background(px[nx, ny]):
                    visited[i2] = 1
                    queue.append((nx, ny))
    alpha = rgba.getchannel("A").filter(ImageFilter.GaussianBlur(0.5))
    rgba.putalpha(alpha)
    return rgba


def align(rgba):
    """裁到非透明包围盒，等比例缩放，让脚底落在 (256, 480) 且水平居中。"""
    bbox = rgba.getchannel("A").getbbox()
    if not bbox:
        raise ValueError("抠图后没有非透明像素，检查背景阈值")
    crop = rgba.crop(bbox)
    cw, ch = crop.size
    scale = TARGET_H / ch
    nw, nh = int(cw * scale), int(ch * scale)
    if nw > MAX_W:
        scale = MAX_W / cw
        nw, nh = int(cw * scale), int(ch * scale)
    resized = crop.resize((nw, nh), Image.LANCZOS)
    out = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    x = (CANVAS - nw) // 2
    y = max(0, ANCHOR_Y - nh)
    out.paste(resized, (x, y), resized)
    return out


def process(path, frame_id):
    im = Image.open(path)
    result = align(remove_background(im))
    os.makedirs(OUT, exist_ok=True)
    target = os.path.join(OUT, "frame-{}.png".format(frame_id))
    result.save(target, "PNG", optimize=True)
    hist = result.getchannel("A").histogram()
    nonzero = sum(hist[1:])
    print("[OK] {} -> {} (alpha 非零 {:.0f}%)".format(
        os.path.basename(path)[:40], os.path.basename(target),
        100 * nonzero / (CANVAS * CANVAS)
    ))


def main():
    args = [a for a in sys.argv[1:] if a != "--batch"]
    is_batch = sys.argv[1:2] == ["--batch"]
    if not is_batch:
        process(args[0], args[1])
        return

    # 优先：并行生成时每张放在 ai_generated/<frameId>/ 子目录，避免时间戳排序错乱
    pairs = []
    for d in sorted(os.listdir(RAW)):
        sub = os.path.join(RAW, d)
        if os.path.isdir(sub):
            pngs = sorted(glob.glob(os.path.join(sub, "*.png")))
            if pngs:
                pairs.append((pngs[0], d))
    if pairs:
        print("[MODE] 子目录映射，共 {} 张".format(len(pairs)))
        for path, fid in pairs:
            process(path, fid)
        return

    if not args:
        raise SystemExit("[FAIL] --batch 需要 frameId 列表，或把图放进 ai_generated/<frameId>/ 子目录")
    ids = args[0].split(",")
    files = sorted(glob.glob(os.path.join(RAW, "*.png")))
    if len(files) < len(ids):
        raise SystemExit("[FAIL] ai_generated 里只有 {} 张，需要 {}".format(len(files), len(ids)))
    if len(files) > len(ids):
        print("[WARN] ai_generated 有 {} 张，按时间顺序只处理前 {} 张".format(len(files), len(ids)))
    for path, fid in zip(files[:len(ids)], ids):
        process(path, fid)


if __name__ == "__main__":
    main()
