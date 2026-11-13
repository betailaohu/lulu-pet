"""生成水豚噜噜占位立绘（纯 Python 标准库，无需 Pillow）。

这些图是**可替换的占位素材**，带斜线纹理以便一眼区分，不是正式角色形象。
正式素材做好后，直接按同名覆盖 frame-<id>.png 即可，无需改任何代码。

用法：
  python generate_placeholders.py
输出：
  当前目录下的 frame-<id>.png（31 张）与 character.png
"""
import os
import struct
import zlib

W = H = 512
OUT = os.path.dirname(os.path.abspath(__file__))

BODY = (185, 138, 98)
HEAD = (200, 154, 114)
EAR = (168, 123, 85)
INNER = (216, 181, 148)
MUZZLE = (219, 182, 146)
NOSE = (107, 74, 53)
EYE = (58, 42, 32)
WHITE = (255, 255, 255)
BLUSH = (233, 166, 160)
BLUE = (120, 180, 220)
PINK = (235, 140, 165)
BROWN = (140, 95, 60)
ORANGE = (235, 165, 80)
LEAF = (110, 160, 90)
YELLOW = (240, 200, 90)
RED = (215, 95, 95)
GRAY = (150, 150, 150)
CLOUD = (235, 238, 240)


def write_png(path, buf):
    raw = b"".join(b"\x00" + bytes(buf[y * W * 4:(y + 1) * W * 4]) for y in range(H))

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    with open(path, "wb") as fh:
        fh.write(b"\x89PNG\r\n\x1a\n")
        fh.write(chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 6, 0, 0, 0)))
        fh.write(chunk(b"IDAT", zlib.compress(raw, 6)))
        fh.write(chunk(b"IEND", b""))


def ellipse(buf, cx, cy, rx, ry, color, alpha=255):
    r, g, b = color
    for y in range(max(0, int(cy - ry - 1)), min(H, int(cy + ry + 2))):
        dy = (y - cy) / ry
        for x in range(max(0, int(cx - rx - 1)), min(W, int(cx + rx + 2))):
            dx = (x - cx) / rx
            if dx * dx + dy * dy <= 1.0:
                i = (y * W + x) * 4
                buf[i], buf[i + 1], buf[i + 2], buf[i + 3] = r, g, b, alpha


def line(buf, x0, y0, x1, y1, color, thick=3):
    steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for k in range(steps + 1):
        t = k / steps if steps else 0
        ellipse(buf, x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, thick, thick, color)


def draw_eyes(buf, dx, dy, expr):
    ex = [205 + dx, 307 + dx]
    ey = 210 + dy
    if expr in ("sleep", "content", "tired", "smug"):
        for x in ex:
            ellipse(buf, x, ey, 15, 3, EYE)
        if expr == "smug":
            line(buf, ex[1] - 14, ey - 14, ex[1] + 14, ey - 20, EYE, 2)
    elif expr == "shock":
        for x in ex:
            ellipse(buf, x, ey, 20, 20, WHITE)
            ellipse(buf, x, ey, 10, 10, EYE)
    elif expr == "wink":
        ellipse(buf, ex[0], ey, 11, 11, EYE)
        ellipse(buf, ex[1], ey, 15, 3, EYE)
    elif expr in ("curious", "confused"):
        ellipse(buf, ex[0], ey, 13, 13, EYE)
        ellipse(buf, ex[1], ey, 8, 8, EYE)
    else:
        for x in ex:
            ellipse(buf, x, ey, 11, 11, EYE)
            ellipse(buf, x - 3, ey - 3, 3, 3, WHITE)
    if expr in ("angry", "worried"):
        for idx, x in enumerate(ex):
            if expr == "angry":
                line(buf, x - 16, ey - 24, x + 14, ey - 32 if idx == 0 else ey - 16, EYE, 2)
            else:
                line(buf, x - 16, ey - 32 if idx == 0 else ey - 16, x + 14, ey - 24, EYE, 2)
    if expr in ("shy", "happy"):
        for x in (160 + dx, 352 + dx):
            ellipse(buf, x, 258 + dy, 22, 11, BLUSH)
    if expr in ("cry", "sweat"):
        ellipse(buf, 205 + dx, 258 + dy, 8, 16, BLUE)
    ellipse(buf, 256 + dx, 292 + dy, 16, 4, NOSE)


def draw_extra(buf, kind, dy):
    if kind == "zzz":
        for x, y in ((380, 118), (406, 92), (432, 66)):
            line(buf, x, y, x + 20, y, (90, 90, 110), 3)
            line(buf, x + 20, y, x, y + 20, (90, 90, 110), 3)
            line(buf, x, y + 20, x + 20, y + 20, (90, 90, 110), 3)
    elif kind == "drop":
        ellipse(buf, 404, 178 + dy, 9, 18, BLUE)
    elif kind == "heart":
        ellipse(buf, 392, 150 + dy, 13, 13, PINK)
        ellipse(buf, 414, 150 + dy, 13, 13, PINK)
        line(buf, 392, 158 + dy, 403, 182 + dy, PINK, 4)
        line(buf, 414, 158 + dy, 403, 182 + dy, PINK, 4)
    elif kind == "bowl":
        ellipse(buf, 402, 192 + dy, 30, 14, BROWN)
        ellipse(buf, 402, 185 + dy, 26, 8, ORANGE)
    elif kind == "cup":
        for yy in range(160, 200):
            line(buf, 384, yy, 420, yy, BROWN, 2)
        line(buf, 420, 168, 432, 168, GRAY, 2)
        line(buf, 432, 168, 432, 192, GRAY, 2)
        line(buf, 432, 192, 420, 192, GRAY, 2)
    elif kind == "ball":
        ellipse(buf, 402, 186 + dy, 20, 20, ORANGE)
    elif kind == "bang":
        line(buf, 400, 130 + dy, 400, 174 + dy, YELLOW, 4)
        ellipse(buf, 400, 190 + dy, 5, 5, YELLOW)
    elif kind == "cross":
        line(buf, 388, 138 + dy, 416, 166 + dy, RED, 3)
        line(buf, 416, 138 + dy, 388, 166 + dy, RED, 3)
    elif kind == "arrow":
        line(buf, 380, 170 + dy, 422, 170 + dy, GRAY, 3)
        line(buf, 422, 170 + dy, 408, 156 + dy, GRAY, 3)
        line(buf, 422, 170 + dy, 408, 184 + dy, GRAY, 3)
    elif kind == "cloud":
        for cx, cy, r in ((380, 160, 18), (402, 150, 22), (424, 160, 18)):
            ellipse(buf, cx, cy + dy, r, r, CLOUD)


def draw(frame_id, expr, dy, extra):
    buf = bytearray(W * H * 4)
    tilt = 6 if expr in ("curious", "confused") else 0
    ellipse(buf, 256, 452 + dy, 150, 16, (0, 0, 0), 38)
    ellipse(buf, 256, 340 + dy, 155, 125, BODY)
    ellipse(buf, 256 + tilt, 230 + dy, 135, 110, HEAD)
    for cx in (155 + tilt, 357 + tilt):
        ellipse(buf, cx, 145 + dy, 28, 28, EAR)
        ellipse(buf, cx, 145 + dy, 15, 15, INNER)
    ellipse(buf, 256 + tilt, 112 + dy, 24, 22, ORANGE)
    ellipse(buf, 256 + tilt, 92 + dy, 12, 6, LEAF)
    ellipse(buf, 256 + tilt, 270 + dy, 62, 38, MUZZLE)
    ellipse(buf, 256 + tilt, 256 + dy, 22, 13, NOSE)
    draw_eyes(buf, tilt, dy, expr)
    if extra:
        draw_extra(buf, extra, dy)
    for y in range(H):
        base = y * W * 4
        for x in range(W):
            i = base + x * 4
            if buf[i + 3] > 0 and (x + y) % 56 < 4:
                buf[i] = int(buf[i] * 0.72)
                buf[i + 1] = int(buf[i + 1] * 0.72)
                buf[i + 2] = int(buf[i + 2] * 0.72)
    write_png(os.path.join(OUT, "frame-{}.png".format(frame_id)), buf)
    return buf


FRAMES = {
    "neutral":  ("normal", 0, None),
    "blink":    ("sleep", 0, None),
    "angry":    ("angry", 0, "cross"),
    "ciallo":   ("wink", 0, None),
    "ciallo-b": ("happy", 0, "heart"),
    "coffee":   ("focused", 0, "cup"),
    "cry":      ("cry", 0, "drop"),
    "feed":     ("happy", 0, "bowl"),
    "fly":      ("happy", -40, "cloud"),
    "goAway":   ("smug", 0, "arrow"),
    "hungry":   ("worried", 0, "bowl"),
    "panic":    ("shock", 0, "drop"),
    "pat":      ("shy", 0, "heart"),
    "pressure": ("worried", 0, "cross"),
    "price":    ("smug", 0, "ball"),
    "rival":    ("angry", 0, "ball"),
    "shock":    ("shock", 0, "bang"),
    "shy":      ("shy", 0, "heart"),
    "sit":      ("content", 8, None),
    "sleep":    ("sleep", 16, "zzz"),
    "smug":     ("smug", 0, None),
    "startle":  ("shock", 0, "bang"),
    "stranded": ("cry", 20, "drop"),
    "stretch":  ("sleep", -8, "zzz"),
    "think":    ("confused", 0, None),
    "toy":      ("happy", 0, "ball"),
    "trip":     ("shock", 12, "bang"),
    "walk":     ("normal", 0, None),
    "walk-b":   ("normal", 6, None),
    "wash":     ("content", 0, "drop"),
    "work":     ("tired", 0, "cup"),
    "dance":    ("happy", 0, "heart"),
    "cheer":    ("happy", 0, "ball"),
    "wonder":   ("curious", 0, None),
    "nap":      ("sleep", 12, "zzz"),
    "jump":     ("happy", -30, "cloud"),
}

if __name__ == "__main__":
    main_buf = None
    for fid, (expr, dy, extra) in FRAMES.items():
        b = draw(fid, expr, dy, extra)
        if fid == "neutral":
            main_buf = b
    write_png(os.path.join(OUT, "character.png"), main_buf)
    print("generated {} frames + character.png in {}".format(len(FRAMES), OUT))
