"""从 .research/templates/deepfish 生成 android/ 工程骨架（幂等，已存在则跳过）。

做的事：
  1. 复制 MIT 模板源码
  2. 改身份：包名 / 应用名 / 主题色 / 常量前缀 / 所有硬编码角色名
  3. 清空上游角色素材（授权隔离），换成本项目占位立绘
  4. 用共享层 manifest.json / state.json 覆盖行为与状态文案
  5. 同步共享配置到 app assets

用法：
  python setup_android.py
"""
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, ".research", "templates", "deepfish")
DST = os.path.join(ROOT, "android")
LULU = os.path.join(ROOT, "assets", "lulu")
SHARED = os.path.join(ROOT, "shared")

TEXT_EXT = {".kt", ".xml", ".gradle", ".kts", ".properties", ".pro", ".md", ".txt", ".json"}

REPLACEMENTS = [
    ("com.deepfish.pet", "com.lulu.pet"),
    ("DeepFish", "Lulu"),
    ("deepfish_", "lulu_"),
    ("fish_blue", "lulu_brown"),
    ("#2E8BEF", "#B98A62"),
    ("蓝色大肥鱼桌宠", "水豚噜噜桌宠"),
    ("大肥鱼桌宠", "水豚噜噜桌宠"),
    ("蓝色大肥鱼", "水豚噜噜"),
    ("大肥鱼", "噜噜"),
    ("寻找白饭", "找草吃"),
]

BEHAVIORS_KT = r'''package com.lulu.pet.model

data class Behavior(
    val id: String,
    val scene: String,
    val expression: String,
    val icon: String,
    val duration: Long,
    val line: String
)

object Behaviors {

    val behaviors: Map<String, Behavior> = listOf(
        Behavior("walk", "walk", "happy", "✦", 7200, "慢慢走一圈，反正也不着急。"),
        Behavior("wash", "wash", "focused", "✦", 5000, "泡个澡，水温刚刚好。"),
        Behavior("work", "work", "tired", "💢", 4500, "……先趴一会儿再说。"),
        Behavior("coffee", "coffee", "focused", "☕", 5200, "喝口热的，困了就睡。"),
        Behavior("toy", "toy", "happy", "♡", 5200, "抱着橘子发会儿呆。"),
        Behavior("sleep", "sleep", "sleep", "Z", 9000, "我先睡了，有事明天讲。"),
        Behavior("dream", "sleep", "sleep", "☆", 7200, "梦里有一整片温泉。"),
        Behavior("hungry", "hungry", "worried", "🍚", 3600, "草……好像还没送来。"),
        Behavior("sit", "sit", "content", "♪", 4800, "坐好了，不动也挺好。"),
        Behavior("pat", "pat", "shy", "♡", 900, "嗯……可以，只许摸一下。"),
        Behavior("shy", "shy", "shy", "♡", 1700, "别、别一直盯着看嘛。"),
        Behavior("trip", "stranded", "shock", "‼", 1200, "啊，脚滑了一下。"),
        Behavior("feed", "feed", "happy", "🍚", 1300, "有吃的？那我不生气了。"),
        Behavior("think", "work", "confused", "?", 1500, "想了三秒，决定放弃思考。"),
        Behavior("smug", "smug", "smug", "✦", 2200, "我什么都不做，也很厉害吧。"),
        Behavior("angry", "angry", "angry", "💢", 2100, "……（缓缓把头转过去）"),
        Behavior("ciallo", "ciallo", "wink", "☆", 1900, "噜～"),
        Behavior("fly", "fly", "happy", "✈", 2400, "偶尔也想蹦一下。"),
        Behavior("price", "price", "smug", "¥", 2300, "我很好养的，一把草就够。"),
        Behavior("panic", "panic", "sweat", "💦", 1900, "稍、稍微有点慌。"),
        Behavior("rival", "rival", "angry", "⚡", 2400, "隔壁那只……算了，不比了。"),
        Behavior("shock", "shock", "shock", "‼", 2500, "诶？"),
        Behavior("pressure", "pressure", "worried", "☁", 2200, "压力？泡个热水就没了。"),
        Behavior("stranded", "stranded", "cry", "💧", 2200, "搁浅了，谁来推我一下。"),
        Behavior("cry", "cry", "cry", "💧", 3800, "……没事，只是眼睛进草了。"),
        Behavior("stretch", "stretch", "sleep", "Z", 1500, "你回来啦，我刚伸完懒腰。"),
        Behavior("startle", "startle", "shock", "‼", 1000, "唔，吓一跳。"),
        Behavior("dizzy", "dizzy", "shock", "✦", 2800, "别转了……头晕。"),
        Behavior("dance", "ciallo", "happy", "♪", 3600, "晃两下，算跳舞了。"),
        Behavior("jump", "fly", "happy", "↑", 2200, "蹦一下，证明还醒着。"),
        Behavior("cheer", "smug", "happy", "🎉", 2600, "做到了，夸我一句就行。"),
        Behavior("wonder", "neutral", "curious", "?", 1800, "嗯？这个角度有点意思。"),
        Behavior("nap", "sleep", "sleep", "Z", 5200, "小眯一会儿，不扣钱的。"),
        Behavior("goAway", "go-away", "smug", "♡", 2100, "去别处玩吧，我要静一静。")
    ).associateBy { it.id }

    val scenePlans = mapOf(
        "sleep" to listOf("sleep", "sleep", "dream", "nap"),
        "morning" to listOf("walk", "stretch", "hungry", "ciallo", "cheer"),
        "focus" to listOf("work", "coffee", "think", "panic", "dance"),
        "lunch" to listOf("hungry", "wash", "feed", "sit", "wonder"),
        "afternoon" to listOf("work", "toy", "walk", "smug", "jump", "dance"),
        "evening" to listOf("walk", "toy", "coffee", "sit", "wonder"),
        "default" to listOf("walk", "toy", "think", "jump")
    )

    fun get(id: String): Behavior = behaviors[id] ?: behaviors.getValue("think")

    fun getPlan(phaseId: String): List<String> =
        (scenePlans[phaseId] ?: scenePlans.getValue("default")).toList()

    fun formatLine(id: String): String = get(id).line

    fun stripHints(text: String): String =
        Regex("[（(][^）)]*[）)]").replace(text, "").replace(Regex("\\s{2,}"), " ").trim()

    fun frameName(name: String): String {
        val aliases = mapOf("dream" to "sleep", "dizzy" to "shock", "jump" to "fly")
        return aliases[name] ?: name
    }
}
'''

BODYCLOCK_KT = r'''package com.lulu.pet.model

import java.util.Calendar

enum class BodyPhase(val id: String, val label: String, val energy: Double, val line: String) {
    SLEEP("sleep", "呼呼大睡", 0.16, "Zzz……先睡了，有事明天讲。"),
    MORNING("morning", "刚刚醒来", 0.58, "早上好，先伸个懒腰。"),
    FOCUS("focus", "慢慢营业", 0.92, "今天也……稍微动一下吧。"),
    LUNCH("lunch", "找草吃", 0.64, "到饭点了，草呢？"),
    AFTERNOON("afternoon", "下午发呆", 0.76, "先假装思考三秒。"),
    EVENING("evening", "陪你加班", 0.72, "夜色不错，一起静一静。"),
    SLEEPY("sleep", "开始犯困", 0.22, "很晚啦，答案明天也不会跑。")
}

object BodyClock {

    private val phases = listOf(
        BodyPhase.SLEEP to 0..6,
        BodyPhase.MORNING to 6..9,
        BodyPhase.FOCUS to 9..12,
        BodyPhase.LUNCH to 12..14,
        BodyPhase.AFTERNOON to 14..18,
        BodyPhase.EVENING to 18..23,
        BodyPhase.SLEEPY to 23..24
    )

    private fun currentHour(): Int = Calendar.getInstance().get(Calendar.HOUR_OF_DAY)

    fun getPhase(): BodyPhase {
        val hour = currentHour()
        return phases.firstOrNull { hour >= it.second.first && hour < it.second.last }?.first ?: BodyPhase.SLEEP
    }

    fun msUntilNextMinute(): Long {
        val now = Calendar.getInstance()
        return 60000L - (now.get(Calendar.SECOND) * 1000L + now.get(Calendar.MILLISECOND))
    }
}
'''


def replace_text_everywhere(base):
    changed = 0
    for dirpath, _, filenames in os.walk(base):
        for name in filenames:
            path = os.path.join(dirpath, name)
            ext = os.path.splitext(name)[1].lower()
            if name in ("LICENSE", "UPSTREAM_README.md") or ext not in TEXT_EXT:
                continue
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    text = fh.read()
            except (UnicodeDecodeError, OSError):
                continue
            new = text
            for old, rep in REPLACEMENTS:
                new = new.replace(old, rep)
            if new != text:
                with open(path, "w", encoding="utf-8", newline="") as fh:
                    fh.write(new)
                changed += 1
    return changed


def main():
    if not os.path.isdir(SRC):
        print("[FAIL] 模板不存在：", SRC)
        sys.exit(1)
    if os.path.isdir(DST):
        print("[SKIP] android/ 已存在，未覆盖。如需重建请先手动删除该目录。")
        sys.exit(0)

    shutil.copytree(SRC, DST)
    print("[1/6] 复制模板 -> android/")

    upstream_readme = os.path.join(DST, "README.md")
    if os.path.isfile(upstream_readme):
        os.rename(upstream_readme, os.path.join(DST, "UPSTREAM_README.md"))

    old_pkg = os.path.join(DST, "app", "src", "main", "java", "com", "deepfish", "pet")
    new_pkg = os.path.join(DST, "app", "src", "main", "java", "com", "lulu", "pet")
    os.makedirs(os.path.join(DST, "app", "src", "main", "java", "com", "lulu"), exist_ok=True)
    if os.path.isdir(old_pkg):
        shutil.move(old_pkg, new_pkg)
        shutil.rmtree(os.path.join(DST, "app", "src", "main", "java", "com", "deepfish"))
    print("[2/6] 源码包路径 com.deepfish.pet -> com.lulu.pet")

    count = replace_text_everywhere(DST)
    print("[3/6] 身份/角色名批量替换：{} 个文件".format(count))

    model_dir = os.path.join(new_pkg, "model")
    with open(os.path.join(model_dir, "Behaviors.kt"), "w", encoding="utf-8", newline="") as fh:
        fh.write(BEHAVIORS_KT)
    with open(os.path.join(model_dir, "BodyClock.kt"), "w", encoding="utf-8", newline="") as fh:
        fh.write(BODYCLOCK_KT)
    print("[4/6] 行为表 / 生理时钟换成水豚噜噜文案")

    frames_dir = os.path.join(DST, "app", "src", "main", "assets", "frames")
    shutil.rmtree(frames_dir, ignore_errors=True)
    os.makedirs(frames_dir, exist_ok=True)
    n = 0
    for name in sorted(os.listdir(LULU)):
        if name.startswith("frame-") and name.endswith(".png"):
            shutil.copy2(os.path.join(LULU, name), os.path.join(frames_dir, name))
            n += 1
    shutil.copy2(os.path.join(LULU, "character.png"),
                 os.path.join(DST, "app", "src", "main", "assets", "character.png"))
    print("[5/6] 清空上游角色素材，写入 {} 张占位立绘 + character.png".format(n))

    assets_dir = os.path.join(DST, "app", "src", "main", "assets")
    for cfg in ("manifest.json", "state.json"):
        shutil.copy2(os.path.join(SHARED, cfg), os.path.join(assets_dir, cfg))
    json.load(open(os.path.join(assets_dir, "manifest.json"), encoding="utf-8"))
    json.load(open(os.path.join(assets_dir, "state.json"), encoding="utf-8"))
    print("[6/6] 同步 shared/manifest.json + state.json 到 app assets（JSON 已校验）")

    print("=== done ===")


if __name__ == "__main__":
    main()
