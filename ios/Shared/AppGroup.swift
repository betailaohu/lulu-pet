import Foundation

/// 主 App 与 Widget Extension 之间唯一的共享通道。
/// 两个 target 的 entitlements 里必须是完全相同的 identifier，写错是小组件空白的最常见原因。
enum AppGroup {
    static let identifier = "group.com.lulu.pet"

    /// 免费 Apple ID 侧载时签名拿不到 App Groups 能力，`UserDefaults(suiteName:)` 会返回 nil。
    /// 这时候退化到 `.standard`：App 内一切照常，只是小组件读不到主 App 的数据（会显示占位快照）。
    static let defaults: UserDefaults? = UserDefaults(suiteName: identifier) ?? .standard

    /// 小组件是否真的能读到共享数据，用来在界面上给出提示
    static var isSharedStoreAvailable: Bool {
        UserDefaults(suiteName: identifier) != nil
    }

    private static let snapshotKey = "lulu.snapshot"

    struct Snapshot: Codable {
        var satiety: Double
        var mood: Double
        var affinity: Double
        var statusText: String
        var frameId: String
        var updatedAt: Date

        static func placeholder() -> Snapshot {
            Snapshot(
                satiety: 70, mood: 75, affinity: 10,
                statusText: "噜噜正在发呆", frameId: "neutral",
                updatedAt: Date()
            )
        }
    }

    static func write(_ snapshot: Snapshot) {
        guard let defaults,
              let data = try? JSONEncoder().encode(snapshot) else { return }
        defaults.set(data, forKey: snapshotKey)
    }

    static func read() -> Snapshot? {
        guard let defaults,
              let data = defaults.data(forKey: snapshotKey) else { return nil }
        return try? JSONDecoder().decode(Snapshot.self, from: data)
    }
}
