"""Kotlin 源码静态粗检（无编译环境下的第一道防线）。

检查：
  - 括号 / 方括号 / 圆括号平衡（跳过注释、字符串、字符字面量）
  - 未闭合的字符串
  - 项目内跨文件引用的常见残留（Behaviors.get / poseVisualScale / clickLines）

用法：python .research/check_kotlin.py
"""
import glob
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JAVA = os.path.join(ROOT, "android", "app", "src", "main", "java")
FILES = sorted(glob.glob(os.path.join(JAVA, "**", "*.kt"), recursive=True))

PAIRS = {"}": "{", ")": "(", "]": "["}
OPEN = set("({[")
CLOSE = set(")}]")


def strip_literals(src):
    out = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c == "/" and i + 1 < n and src[i + 1] == "/":
            while i < n and src[i] != "\n":
                i += 1
            continue
        if c == "/" and i + 1 < n and src[i + 1] == "*":
            i += 2
            while i + 1 < n and not (src[i] == "*" and src[i + 1] == "/"):
                i += 1
            i += 2
            continue
        if c == '"':
            i += 1
            closed = False
            while i < n:
                if src[i] == "\\":
                    i += 2
                    continue
                if src[i] == '"':
                    i += 1
                    closed = True
                    break
                i += 1
            out.append('""' if closed else '"')
            if not closed:
                out.append("__UNCLOSED_STRING__")
            continue
        if c == "'":
            i += 1
            while i < n:
                if src[i] == "\\":
                    i += 2
                    continue
                if src[i] == "'":
                    i += 1
                    break
                i += 1
            out.append("''")
            continue
        out.append(c)
        i += 1
    return "".join(out)


failures = 0
for path in FILES:
    rel = os.path.relpath(path, ROOT).replace("\\", "/")
    text = strip_literals(open(path, encoding="utf-8").read())
    if "__UNCLOSED_STRING__" in text:
        print("[FAIL 字符串未闭合]", rel)
        failures += 1
        continue
    stack = []
    ok = True
    for ch in text:
        if ch in OPEN:
            stack.append(ch)
        elif ch in CLOSE:
            if not stack or stack[-1] != PAIRS[ch]:
                ok = False
                break
            stack.pop()
    if not ok or stack:
        print("[FAIL 括号不平衡]", rel, "剩余", len(stack))
        failures += 1

for path in FILES:
    rel = os.path.relpath(path, ROOT).replace("\\", "/")
    src = open(path, encoding="utf-8").read()
    for bad in ("Behaviors.get(", "Behaviors.getPlan(", "poseVisualScale(", "clickLines"):
        if bad in src:
            # 注释里出现不算问题
            for line in src.splitlines():
                if bad in line and not line.strip().startswith(("//", "*", "/*")):
                    print("[WARN 残留引用]", rel, "->", bad, "|", line.strip()[:90])

print("checked {} Kotlin files, {} structural failures".format(len(FILES), failures))
