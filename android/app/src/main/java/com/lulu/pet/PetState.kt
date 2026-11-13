package com.lulu.pet

import android.content.Context
import android.content.SharedPreferences
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * 养成数值：饱食度 / 心情 / 亲密度。
 *
 * 配置来自共享层 state.json（读失败时用内置默认值），数值持久化在 SharedPreferences，
 * 按 decayPerHour 随真实时间衰减。由 PetService.onCreate() 调用 init()。
 * 小组件数据源后续可通过 snapshot() 接 App Group / WidgetCenter。
 */
object PetState {

    private const val FILE = "lulu_state"
    private const val KEY_SATIETY = "satiety"
    private const val KEY_MOOD = "mood"
    private const val KEY_AFFINITY = "affinity"
    private const val KEY_LAST = "lastTick"
    private const val KEY_DAY = "affinityDay"
    private const val KEY_DAY_GAIN = "affinityGainToday"

    data class Config(
        val satietyMax: Int = 100,
        val satietyInitial: Int = 70,
        val satietyDecay: Double = 6.0,
        val satietyLow: Int = 30,
        val satietyLowBehavior: String = "hungry",
        val moodMax: Int = 100,
        val moodInitial: Int = 75,
        val moodDecay: Double = 3.0,
        val moodLow: Int = 25,
        val moodLowBehavior: String = "cry",
        val affinityMax: Int = 100,
        val affinityInitial: Int = 10,
        val gainPerPat: Int = 1,
        val gainPerFeed: Int = 3,
        val maxGainPerDay: Int = 20
    )

    private var prefs: SharedPreferences? = null
    private var cfg = Config()
    private var texts = listOf(
        "噜噜有点饿了", "噜噜在打瞌睡", "噜噜有点低落", "噜噜今天很松弛", "噜噜正在发呆"
    )

    fun init(context: Context) {
        val app = context.applicationContext
        prefs = app.getSharedPreferences(FILE, Context.MODE_PRIVATE)
        loadConfig(app)
        val p = prefs ?: return
        if (!p.contains(KEY_SATIETY)) {
            p.edit()
                .putFloat(KEY_SATIETY, cfg.satietyInitial.toFloat())
                .putFloat(KEY_MOOD, cfg.moodInitial.toFloat())
                .putFloat(KEY_AFFINITY, cfg.affinityInitial.toFloat())
                .putLong(KEY_LAST, System.currentTimeMillis())
                .apply()
        }
        tick()
    }

    private fun loadConfig(context: Context) {
        runCatching {
            val root = JSONObject(
                context.assets.open("state.json").bufferedReader().use { it.readText() }
            )
            val s = root.getJSONObject("stats")
            val sa = s.getJSONObject("satiety")
            val mo = s.getJSONObject("mood")
            val af = s.getJSONObject("affinity")
            cfg = Config(
                satietyMax = sa.optInt("max", 100),
                satietyInitial = sa.optInt("initial", 70),
                satietyDecay = sa.optDouble("decayPerHour", 6.0),
                satietyLow = sa.optInt("lowThreshold", 30),
                satietyLowBehavior = sa.optString("lowBehavior", "hungry"),
                moodMax = mo.optInt("max", 100),
                moodInitial = mo.optInt("initial", 75),
                moodDecay = mo.optDouble("decayPerHour", 3.0),
                moodLow = mo.optInt("lowThreshold", 25),
                moodLowBehavior = mo.optString("lowBehavior", "cry"),
                affinityMax = af.optInt("max", 100),
                affinityInitial = af.optInt("initial", 10),
                gainPerPat = af.optInt("gainPerPat", 1),
                gainPerFeed = af.optInt("gainPerFeed", 3),
                maxGainPerDay = af.optInt("maxGainPerDay", 20)
            )
            val arr = root.optJSONArray("statusText")
            if (arr != null && arr.length() >= 5) {
                texts = (0 until arr.length()).map {
                    arr.getJSONObject(it).optString("text")
                }
            }
        }
    }

    /** 按距上次结算的真实小时数衰减数值。 */
    private fun tick() {
        val p = prefs ?: return
        val now = System.currentTimeMillis()
        val last = p.getLong(KEY_LAST, now)
        val hours = ((now - last) / 3_600_000.0).coerceAtLeast(0.0)
        if (hours <= 0.0) return
        val satiety = (p.getFloat(KEY_SATIETY, cfg.satietyInitial.toFloat())
                - (cfg.satietyDecay * hours).toFloat())
            .coerceIn(0f, cfg.satietyMax.toFloat())
        val mood = (p.getFloat(KEY_MOOD, cfg.moodInitial.toFloat())
                - (cfg.moodDecay * hours).toFloat())
            .coerceIn(0f, cfg.moodMax.toFloat())
        p.edit()
            .putFloat(KEY_SATIETY, satiety)
            .putFloat(KEY_MOOD, mood)
            .putLong(KEY_LAST, now)
            .apply()
    }

    /** 单击摸头。 */
    fun onPat() {
        val p = prefs ?: return
        tick()
        val e = p.edit()
        val mood = (p.getFloat(KEY_MOOD, cfg.moodInitial.toFloat()) + 2f)
            .coerceAtMost(cfg.moodMax.toFloat())
        e.putFloat(KEY_MOOD, mood)
        e.putFloat(KEY_AFFINITY, addAffinity(e, cfg.gainPerPat))
        e.apply()
    }

    /** 喂食（通过 onCommand("feed") 触发）。 */
    fun onFeed() {
        val p = prefs ?: return
        tick()
        val e = p.edit()
        val satiety = (p.getFloat(KEY_SATIETY, cfg.satietyInitial.toFloat()) + 20f)
            .coerceAtMost(cfg.satietyMax.toFloat())
        val mood = (p.getFloat(KEY_MOOD, cfg.moodInitial.toFloat()) + 3f)
            .coerceAtMost(cfg.moodMax.toFloat())
        e.putFloat(KEY_SATIETY, satiety)
        e.putFloat(KEY_MOOD, mood)
        e.putFloat(KEY_AFFINITY, addAffinity(e, cfg.gainPerFeed))
        e.apply()
    }

    /** 亲密度每日增长上限，避免一直点刷满。 */
    private fun addAffinity(e: SharedPreferences.Editor, gain: Int): Float {
        val p = prefs ?: return cfg.affinityInitial.toFloat()
        val day = SimpleDateFormat("yyyyMMdd", Locale.getDefault()).format(Date())
        val gainedToday = if (day == p.getString(KEY_DAY, "")) p.getInt(KEY_DAY_GAIN, 0) else 0
        val allowed = gain.coerceAtMost((cfg.maxGainPerDay - gainedToday).coerceAtLeast(0))
        e.putString(KEY_DAY, day).putInt(KEY_DAY_GAIN, gainedToday + allowed)
        return (p.getFloat(KEY_AFFINITY, cfg.affinityInitial.toFloat()) + allowed)
            .coerceAtMost(cfg.affinityMax.toFloat())
    }

    /** 数值过低时优先播放的行为，空闲调度会插队。 */
    fun urgentBehavior(): String? {
        val p = prefs ?: return null
        tick()
        return when {
            p.getFloat(KEY_SATIETY, cfg.satietyInitial.toFloat()) < cfg.satietyLow ->
                cfg.satietyLowBehavior
            p.getFloat(KEY_MOOD, cfg.moodInitial.toFloat()) < cfg.moodLow ->
                cfg.moodLowBehavior
            else -> null
        }
    }

    /** 供小组件显示的状态文案，文案来自 state.json#statusText。 */
    fun statusText(isSleepPhase: Boolean = false): String {
        val p = prefs ?: return texts.last()
        tick()
        val satiety = p.getFloat(KEY_SATIETY, cfg.satietyInitial.toFloat())
        val mood = p.getFloat(KEY_MOOD, cfg.moodInitial.toFloat())
        val idx = when {
            satiety < cfg.satietyLow -> 0
            isSleepPhase -> 1
            mood < cfg.moodLow -> 2
            mood >= 70 -> 3
            else -> 4
        }
        return texts.getOrElse(idx) { texts.last() }
    }

    /** 预留给小组件 / 设置页的数据出口。 */
    fun snapshot(): Map<String, Float> {
        val p = prefs ?: return emptyMap()
        tick()
        return mapOf(
            "satiety" to p.getFloat(KEY_SATIETY, cfg.satietyInitial.toFloat()),
            "mood" to p.getFloat(KEY_MOOD, cfg.moodInitial.toFloat()),
            "affinity" to p.getFloat(KEY_AFFINITY, cfg.affinityInitial.toFloat())
        )
    }
}
