"""把未做 AI 生成的帧按语义复用已有 AI 帧，补齐 36 张，并记录素材来源。

用法：python fill_remaining.py
输出：ai_processed/ 下 36 张 frame-*.png + character.png + asset_provenance.json
"""
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
PROCESSED = os.path.join(HERE, "ai_processed")
MANIFEST = os.path.join(HERE, "..", "..", "shared", "manifest.json")

# 15 张由 ImageGen 生成并经 process_ai_assets.py 抠图对齐的核心帧
AI_FRAMES = [
    "blink", "feed", "hungry", "nap", "neutral", "pat", "shy", "sit",
    "sleep", "startle", "stretch", "think", "walk", "walk-b", "wonder",
]

# 其余 21 张复用语义最接近的 AI 帧；后续可逐张单独重绘后覆盖同名文件
REUSE = {
    "angry": "startle",
    "ciallo": "sit",
    "ciallo-b": "pat",
    "coffee": "think",
    "cry": "shy",
    "fly": "stretch",
    "goAway": "walk-b",
    "panic": "startle",
    "pressure": "think",
    "price": "sit",
    "rival": "startle",
    "shock": "startle",
    "smug": "sit",
    "stranded": "stretch",
    "toy": "feed",
    "trip": "startle",
    "wash": "sleep",
    "work": "think",
    "dance": "pat",
    "cheer": "pat",
    "jump": "startle",
}

PROVENANCE = {
    "method": "web 形象调研 + AI 生成核心帧 + 语义复用补齐",
    "sourceResearch": {
        "ip": "水豚噜噜（Capylulu / 噜噜）",
        "copyrightHolder": "铁罐(北京)文化传媒有限公司",
        "origin": "动画《平头哥》少年篇配角，2024 年 3 月推出",
        "visualTraits": [
            "圆滚滚的奶黄 / 浅棕色身体（芒果般造型）",
            "头顶一颗带绿叶的小橘子",
            "大而黑的眼睛、短小四肢、宽平口鼻",
            "标志性漏齿笑",
            "佛系淡定、慢条斯理，喜欢泡温泉、吃橘子、吃冰淇淋",
        ],
        "references": [
            "https://baike.baidu.com/item/%E6%B0%B4%E8%B1%9A%E5%99%9C%E5%99%9C/66823728",
            "https://www.wikizero.org/wiki/zh/%E6%B0%B4%E8%B1%9A%E5%99%9C%E5%99%9C",
            "https://m.toutiao.com/article/7658550916395663914",
        ],
        "usage": "web 仅用于提取形象设定与气质参考；没有下载或复制任何官方 / 同人成品图片。",
    },
    "aiGenerated": AI_FRAMES,
    "reused": REUSE,
    "postProcess": "process_ai_assets.py：flood-fill 抠白底 → 缩放到 512x512 → 脚底对齐 (256,480)",
    "licenseNote": (
        "本项目定位为非商业、非官方同人作品。AI 生成图是风格近似的原创绘制，"
        "不是官方素材，不包含任何从网络抓取的成品图。若日后计划商业化或公开分发，"
        "须先取得版权方授权并改用官方素材。"
    ),
}


def main():
    expected = set(json.load(open(MANIFEST, encoding="utf-8"))["frameFiles"])

    for fid in AI_FRAMES:
        p = os.path.join(PROCESSED, "frame-{}.png".format(fid))
        if not os.path.isfile(p):
            raise SystemExit("[FAIL] 缺少 AI 帧: " + p)

    for fid, src in REUSE.items():
        shutil.copy2(
            os.path.join(PROCESSED, "frame-{}.png".format(src)),
            os.path.join(PROCESSED, "frame-{}.png".format(fid)),
        )

    shutil.copy2(
        os.path.join(PROCESSED, "frame-neutral.png"),
        os.path.join(PROCESSED, "character.png"),
    )

    with open(os.path.join(PROCESSED, "asset_provenance.json"), "w", encoding="utf-8") as fh:
        json.dump(PROVENANCE, fh, ensure_ascii=False, indent=2)

    got = {
        n[len("frame-"):-4]
        for n in os.listdir(PROCESSED)
        if n.startswith("frame-") and n.endswith(".png")
    }
    missing = sorted(expected - got)
    extra = sorted(got - expected)
    print("AI 生成 {} 张，复用 {} 张，合计 {} 张".format(
        len(AI_FRAMES), len(REUSE), len(got)
    ))
    print("缺失:", missing or "无", "| 多余:", extra or "无")
    if missing:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
