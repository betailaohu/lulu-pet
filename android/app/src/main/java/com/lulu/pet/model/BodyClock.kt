package com.lulu.pet.model

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
