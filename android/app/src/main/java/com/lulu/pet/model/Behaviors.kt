package com.lulu.pet.model

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
