package com.lulu.pet.model

import android.content.Context
import org.json.JSONObject

/**
 * 共享层 manifest.json 的运行时读取器。
 *
 * 读取失败时全部回退到 Behaviors.kt 的硬编码表，保证桌宠不会因为配置文件损坏而空白/崩溃。
 * 由 PetService.onCreate() 调用 init()，一定早于 PetView 的任何一次 setFrame()。
 */
object PetManifest {

    data class FrameLoop(val frames: Array<String>, val intervals: IntArray)

    private var behaviors: Map<String, Behavior> = emptyMap()
    private var plans: Map<String, List<String>> = emptyMap()
    private var aliases: Map<String, String> = emptyMap()
    private var poseScales: Map<String, Float> = emptyMap()
    private var poseDefault = 1f
    private var loops: Map<String, FrameLoop> = emptyMap()
    private var restingDefault = "neutral"
    private var restingSleep = "sleep"
    private var frameFiles: Set<String> = emptySet()
    private var loaded = false

    val isLoaded: Boolean get() = loaded

    fun init(context: Context) {
        runCatching {
            val root = JSONObject(
                context.assets.open("manifest.json").bufferedReader().use { it.readText() }
            )

            val bObj = root.getJSONObject("behaviors")
            val bMap = mutableMapOf<String, Behavior>()
            for (id in bObj.keys()) {
                val o = bObj.getJSONObject(id)
                bMap[id] = Behavior(
                    id = id,
                    scene = o.optString("scene"),
                    expression = o.optString("expression"),
                    icon = o.optString("icon"),
                    duration = o.optLong("duration"),
                    line = o.optString("line")
                )
            }

            val pObj = root.getJSONObject("scenePlans")
            val pMap = mutableMapOf<String, List<String>>()
            for (k in pObj.keys()) {
                val arr = pObj.getJSONArray(k)
                pMap[k] = (0 until arr.length()).map { arr.getString(it) }
            }

            val aObj = root.optJSONObject("frameAliases")
            val aMap = mutableMapOf<String, String>()
            if (aObj != null) {
                for (k in aObj.keys()) aMap[k] = aObj.getString(k)
            }

            val ps = root.optJSONObject("poseScale")
            val sMap = mutableMapOf<String, Float>()
            var sDefault = 1f
            if (ps != null) {
                val groups = ps.optJSONArray("groups")
                if (groups != null) {
                    for (g in 0 until groups.length()) {
                        val o = groups.getJSONObject(g)
                        val value = o.optDouble("value", 1.0).toFloat()
                        val ids = o.optJSONArray("ids") ?: continue
                        for (i in 0 until ids.length()) sMap[ids.getString(i)] = value
                    }
                }
                sDefault = ps.optDouble("default", 1.0).toFloat()
            }

            val mf = root.optJSONObject("multiFrameActions")
            val lMap = mutableMapOf<String, FrameLoop>()
            if (mf != null) {
                for (k in mf.keys()) {
                    val o = mf.getJSONObject(k)
                    val fArr = o.getJSONArray("frames")
                    val iArr = o.getJSONArray("intervals")
                    lMap[k] = FrameLoop(
                        Array(fArr.length()) { fArr.getString(it) },
                        IntArray(iArr.length()) { iArr.getInt(it) }
                    )
                }
            }

            val rf = root.optJSONObject("restingFrame")
            if (rf != null) {
                restingDefault = rf.optString("default", "neutral")
                restingSleep = rf.optString("sleep", "sleep")
            }

            val ff = root.optJSONArray("frameFiles")
            val fSet = mutableSetOf<String>()
            if (ff != null) {
                for (i in 0 until ff.length()) fSet.add(ff.getString(i))
            }

            behaviors = bMap
            plans = pMap
            aliases = aMap
            poseScales = sMap
            poseDefault = sDefault
            loops = lMap
            frameFiles = fSet
            loaded = true
        }
    }

    private fun table(): Map<String, Behavior> =
        if (loaded) behaviors else Behaviors.behaviors

    fun get(id: String): Behavior {
        val src = table()
        return src[id] ?: src.getValue("think")
    }

    fun getPlan(phaseId: String): List<String> {
        val src = if (loaded) plans else Behaviors.scenePlans
        return (src[phaseId] ?: src.getValue("default")).toList()
    }

    fun frameName(name: String): String =
        (if (loaded) aliases[name] else null) ?: Behaviors.frameName(name)

    fun poseScale(frame: String): Float =
        if (loaded) (poseScales[frame] ?: poseDefault) else legacyPoseScale(frame)

    fun multiFrameAction(name: String): FrameLoop? =
        if (loaded) loops[name] else legacyLoop(name)

    fun restingFrame(isSleep: Boolean): String =
        if (isSleep) restingSleep else restingDefault

    fun hasFrame(name: String): Boolean =
        if (loaded && frameFiles.isNotEmpty()) frameFiles.contains(name) else true

    private fun legacyLoop(name: String): FrameLoop? = when (name) {
        "ciallo" -> FrameLoop(arrayOf("ciallo", "ciallo-b"), intArrayOf(420, 420))
        "dance" -> FrameLoop(
            arrayOf("ciallo", "ciallo-b", "smug", "ciallo-b"),
            intArrayOf(300, 300, 380, 300)
        )
        else -> null
    }

    private fun legacyPoseScale(frame: String): Float = when (frame) {
        "curious" -> 1.05f
        "shy", "wave", "ciallo", "goAway" -> 0.89f
        "happy", "excited", "price", "toy", "pat", "feed", "smug",
        "walk", "walk-b" -> 0.92f
        "surprised", "shock", "panic", "trip", "stranded", "startle", "angry", "rival",
        "pressure", "sleepy", "sleep", "stretch", "work", "wash", "coffee", "hungry",
        "think" -> 0.91f
        "jump", "fly" -> 0.84f
        else -> 1f
    }
}
