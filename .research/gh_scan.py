"""GitHub 开源桌宠项目调研脚本（可重复运行）。

用法：
  python gh_scan.py
输出：按关键词搜索仓库 + 重点仓库的元数据（star / 语言 / 协议 / 最后提交）。
"""
import json
import urllib.error
import urllib.parse
import urllib.request

UA = {"User-Agent": "workbuddy-desktop-pet-research"}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)


def line(r):
    return "  {:<48} *{:<5} {:<12} {:<10} {} | {}".format(
        r["full_name"][:48],
        r["stargazers_count"],
        (r.get("language") or "-")[:12],
        ((r.get("license") or {}).get("spdx_id") or "-")[:10],
        r["pushed_at"][:10],
        (r.get("description") or "")[:78],
    )


QUERIES = [
    "shimeji android pet",
    "desktop pet kotlin compose",
    "widgetkit pet swiftui",
    "桌宠 悬浮窗",
]

REPOS = [
    "Farewell-coder/Dollhouse",
    "fvfpq/deepfish-desktop-pet-android",
    "qimuhewu/desktop-pet",
    "HELPMEEADICE/BANDORI-PET-Android",
    "krystalqiye-lj/VRS-Desktop-Pet",
    "DYXDQ/arkpets-lite",
    "VidiPT89/iVidigotchy",
    "7l-ui/whalegirl-pet",
    "CianLaw/pet-agent",
    "qingchenyouforcc/NeurolingsCE",
    "youzeFix/Desktopet",
    "telecom888/Live2dOnAndroid",
]

print("=" * 110)
print("一、关键词搜索")
print("=" * 110)
for q in QUERIES:
    print("\n### " + q)
    try:
        url = ("https://api.github.com/search/repositories?q="
               + urllib.parse.quote(q)
               + "&sort=stars&order=desc&per_page=8")
        for r in get(url)["items"]:
            print(line(r))
    except urllib.error.HTTPError as e:
        print("  [搜索被限流] HTTP", e.code)
    except Exception as e:
        print("  [失败]", e)

print("\n" + "=" * 110)
print("二、重点仓库元数据")
print("=" * 110)
for full in REPOS:
    try:
        print(line(get("https://api.github.com/repos/" + full)))
    except urllib.error.HTTPError as e:
        print("  {:<48} [HTTP {}]".format(full, e.code))
    except Exception as e:
        print("  {:<48} [失败] {}".format(full, e))
