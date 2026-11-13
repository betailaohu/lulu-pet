import Foundation
import Combine
import WidgetKit

/// iOS 侧养成状态机，与 Android 的 PetState.kt 语义对齐：
/// 同一份 shared/state.json，饱食度/心情按小时衰减，摸头/喂食涨亲密度（每日上限）。
/// 每次状态变化都写 App Group 快照并刷新小组件 Timeline。
final class PetState: ObservableObject {

    @Published private(set) var satiety: Double = 70
    @Published private(set) var mood: Double = 75
    @Published private(set) var affinity: Double = 10
    @Published private(set) var frameId: String = "neutral"
    @Published private(set) var statusText: String = "噜噜正在发呆"
    @Published private(set) var bubble: String?

    let manifest: PetManifest?
    private let defaults: UserDefaults? = AppGroup.defaults
    private var cfg = Config()
    private var texts = [
        "噜噜有点饿了", "噜噜在打瞌睡", "噜噜有点低落", "噜噜今天很松弛", "噜噜正在发呆"
    ]
    private var bubbleTimer: Timer?

    private struct Config {
        var satietyInitial: Double = 70
        var satietyDecay: Double = 6
        var satietyLow: Double = 30
        var satietyLowBehavior = "hungry"
        var moodInitial: Double = 75
        var moodDecay: Double = 3
        var moodLow: Double = 25
        var moodLowBehavior = "cry"
        var affinityInitial: Double = 10
        var gainPerPat: Double = 1
        var gainPerFeed: Double = 3
        var maxGainPerDay: Double = 20
    }

    private enum Key {
        static let satiety = "lulu.satiety"
        static let mood = "lulu.mood"
        static let affinity = "lulu.affinity"
        static let lastTick = "lulu.lastTick"
        static let day = "lulu.affinityDay"
        static let dayGain = "lulu.affinityGainToday"
    }

    init() {
        manifest = PetManifest.load()
        loadConfig()
        if defaults?.object(forKey: Key.satiety) == nil {
            defaults?.set(cfg.satietyInitial, forKey: Key.satiety)
            defaults?.set(cfg.moodInitial, forKey: Key.mood)
            defaults?.set(cfg.affinityInitial, forKey: Key.affinity)
            defaults?.set(Date().timeIntervalSince1970, forKey: Key.lastTick)
        }
        satiety = defaults?.double(forKey: Key.satiety) ?? cfg.satietyInitial
        mood = defaults?.double(forKey: Key.mood) ?? cfg.moodInitial
        affinity = defaults?.double(forKey: Key.affinity) ?? cfg.affinityInitial
        tick()
        frameId = manifest?.restingFrame.defaultFrame ?? "neutral"
        statusText = computeStatusText()
        publish()
    }

    // MARK: - 配置（读 shared/state.json，失败则用内置默认值）

    // Reconcile elapsed time when active, then update shared snapshots.
    func refresh() {
        tick()
        statusText = computeStatusText()
        publish()
    }

    private func loadConfig() {
        guard let url = Bundle.main.url(forResource: "state", withExtension: "json"),
              let data = try? Data(contentsOf: url),
              let root = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let stats = root["stats"] as? [String: Any] else { return }

        if let s = stats["satiety"] as? [String: Any] {
            cfg.satietyInitial = s["initial"] as? Double ?? cfg.satietyInitial
            cfg.satietyDecay = s["decayPerHour"] as? Double ?? cfg.satietyDecay
            if let v = s["lowThreshold"] as? Int { cfg.satietyLow = Double(v) }
            cfg.satietyLowBehavior = s["lowBehavior"] as? String ?? cfg.satietyLowBehavior
        }
        if let m = stats["mood"] as? [String: Any] {
            cfg.moodInitial = m["initial"] as? Double ?? cfg.moodInitial
            cfg.moodDecay = m["decayPerHour"] as? Double ?? cfg.moodDecay
            if let v = m["lowThreshold"] as? Int { cfg.moodLow = Double(v) }
            cfg.moodLowBehavior = m["lowBehavior"] as? String ?? cfg.moodLowBehavior
        }
        if let a = stats["affinity"] as? [String: Any] {
            cfg.affinityInitial = a["initial"] as? Double ?? cfg.affinityInitial
            if let v = a["gainPerPat"] as? Int { cfg.gainPerPat = Double(v) }
            if let v = a["gainPerFeed"] as? Int { cfg.gainPerFeed = Double(v) }
            if let v = a["maxGainPerDay"] as? Int { cfg.maxGainPerDay = Double(v) }
        }
        if let arr = root["statusText"] as? [[String: Any]] {
            let t = arr.compactMap { $0["text"] as? String }
            if t.count >= 5 { texts = t }
        }
    }

    // MARK: - 数值

    private func tick() {
        let now = Date().timeIntervalSince1970
        let last = defaults?.double(forKey: Key.lastTick) ?? now
        let hours = max(0, (now - last) / 3600)
        guard hours > 0 else { return }
        satiety = max(0, satiety - cfg.satietyDecay * hours)
        mood = max(0, mood - cfg.moodDecay * hours)
        persist()
    }

    private func persist() {
        defaults?.set(satiety, forKey: Key.satiety)
        defaults?.set(mood, forKey: Key.mood)
        defaults?.set(affinity, forKey: Key.affinity)
        defaults?.set(Date().timeIntervalSince1970, forKey: Key.lastTick)
    }

    private func gainWithDailyCap(_ gain: Double) -> Double {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyyMMdd"
        let day = formatter.string(from: Date())
        let stored = defaults?.string(forKey: Key.day) ?? ""
        let gained = stored == day ? (defaults?.double(forKey: Key.dayGain) ?? 0) : 0
        let allowed = min(gain, max(0, cfg.maxGainPerDay - gained))
        defaults?.set(day, forKey: Key.day)
        defaults?.set(gained + allowed, forKey: Key.dayGain)
        return allowed
    }

    private func computeStatusText() -> String {
        let idx: Int
        if satiety < cfg.satietyLow { idx = 0 }
        else if isSleepPhase() { idx = 1 }
        else if mood < cfg.moodLow { idx = 2 }
        else if mood >= 70 { idx = 3 }
        else { idx = 4 }
        return texts.indices.contains(idx) ? texts[idx] : (texts.last ?? "噜噜正在发呆")
    }

    private func isSleepPhase() -> Bool {
        let hour = Calendar.current.component(.hour, from: Date())
        return hour >= 0 && hour < 6
    }

    /// 数值过低时优先播放的行为，供空闲调度插队（对齐 Android PetState.urgentBehavior）
    func urgentBehavior() -> String? {
        if satiety < cfg.satietyLow { return cfg.satietyLowBehavior }
        if mood < cfg.moodLow { return cfg.moodLowBehavior }
        return nil
    }

    // MARK: - 互动

    func pat() {
        tick()
        mood = min(100, mood + 2)
        affinity = min(100, affinity + gainWithDailyCap(cfg.gainPerPat))
        persist()
        statusText = computeStatusText()
        play("pat")
    }

    func feed() {
        tick()
        satiety = min(100, satiety + 20)
        mood = min(100, mood + 3)
        affinity = min(100, affinity + gainWithDailyCap(cfg.gainPerFeed))
        persist()
        statusText = computeStatusText()
        play("feed")
    }

    /// 切一张状态立绘 + 台词气泡，duration 后回到待机帧
    func play(_ id: String) {
        guard let manifest, let behavior = manifest.behaviors[id] else { return }
        frameId = manifest.frame(for: id)
        bubble = behavior.line.isEmpty ? nil : behavior.line
        bubbleTimer?.invalidate()
        let seconds = max(0.8, Double(behavior.duration) / 1000.0)
        bubbleTimer = Timer.scheduledTimer(withTimeInterval: seconds, repeats: false) { [weak self] _ in
            DispatchQueue.main.async {
                guard let self else { return }
                self.frameId = self.manifest?.restingFrame.defaultFrame ?? "neutral"
                self.bubble = nil
                self.publish()
            }
        }
        publish()
    }

    // MARK: - 同步到小组件 / 灵动岛

    func snapshot() -> AppGroup.Snapshot {
        AppGroup.Snapshot(
            satiety: satiety, mood: mood, affinity: affinity,
            statusText: statusText, frameId: frameId, updatedAt: Date()
        )
    }

    func publish() {
        let value = snapshot()
        AppGroup.write(value)
        WidgetCenter.shared.reloadAllTimelines()
        if #available(iOS 16.1, *) {
            PetLiveActivityManager.startOrUpdate(snapshot: value)
        }
    }

    func endLiveActivity() {
        if #available(iOS 16.1, *) {
            PetLiveActivityManager.end()
        }
    }

    /// 设置页的「恢复初始值」
    func reset() {
        satiety = cfg.satietyInitial
        mood = cfg.moodInitial
        affinity = cfg.affinityInitial
        defaults?.set(0, forKey: Key.dayGain)
        persist()
        statusText = computeStatusText()
        frameId = manifest?.restingFrame.defaultFrame ?? "neutral"
        bubble = nil
        publish()
    }
}
