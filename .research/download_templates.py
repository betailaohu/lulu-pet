"""从 codeload.github.com 下载开源桌宠模板并解压（绕开 github.com 直连受限的环境）。

用法：
  python download_templates.py
会把仓库内容解压到 .research/templates/<别名>/，去掉 GitHub zip 的顶层目录。
"""
import io
import json
import os
import urllib.request
import zipfile

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
UA = {"User-Agent": "workbuddy-desktop-pet-research"}

REPOS = [
    ("pinghub25/pixel-pals", "pixel-pals"),
    ("fvfpq/deepfish-desktop-pet-android", "deepfish"),
    ("qimuhewu/desktop-pet", "mobile-desktop-pet"),
    ("Farewell-coder/Dollhouse", "Dollhouse"),
]


def fetch(url, timeout=90):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def default_branch(full):
    meta = json.loads(fetch("https://api.github.com/repos/" + full, timeout=30))
    return meta["default_branch"]


os.makedirs(BASE, exist_ok=True)
for full, alias in REPOS:
    target = os.path.join(BASE, alias)
    if os.path.isdir(target) and os.listdir(target):
        print("[SKIP] {} already exists".format(alias))
        continue
    try:
        branch = default_branch(full)
        url = "https://codeload.github.com/{}/zip/refs/heads/{}".format(full, branch)
        raw = fetch(url)
        zf = zipfile.ZipFile(io.BytesIO(raw))
        os.makedirs(target, exist_ok=True)
        count = 0
        for info in zf.infolist():
            parts = info.filename.split("/")
            rel = "/".join(parts[1:])
            if not rel or ".." in rel.split("/"):
                continue
            out = os.path.join(target, rel)
            if info.is_dir():
                os.makedirs(out, exist_ok=True)
                continue
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(out, "wb") as fh:
                fh.write(zf.read(info))
            count += 1
        print("[OK] {} <- {} ({} files, {:.1f} KB)".format(alias, full, count, len(raw) / 1024))
    except Exception as exc:
        print("[FAIL] {}: {}".format(full, exc))

print("=== done ===")
