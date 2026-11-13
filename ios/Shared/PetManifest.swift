import Foundation

/// shared/manifest.json 的 Codable 读取器。
/// 与 Android 的 PetManifest.kt 读的是同一份文件，行为 id / 帧名 / 时段池语义一致。
struct PetManifest: Codable {
    let frameFiles: [String]
    let frameAliases: [String: String]
    let restingFrame: RestingFrame
    let behaviors: [String: Behavior]
    let scenePlans: [String: [String]]

    struct RestingFrame: Codable {
        let defaultFrame: String
        let sleepFrame: String

        enum CodingKeys: String, CodingKey {
            case defaultFrame = "default"
            case sleepFrame = "sleep"
        }
    }

    struct Behavior: Codable {
        let scene: String
        let expression: String
        let icon: String
        let duration: Int
        let line: String
        let frame: String
    }

    static func load() -> PetManifest? {
        guard let url = Bundle.main.url(forResource: "manifest", withExtension: "json"),
              let data = try? Data(contentsOf: url) else { return nil }
        return try? JSONDecoder().decode(PetManifest.self, from: data)
    }

    /// behaviorId -> 帧名（先取 behaviors[id].frame，再套 frameAliases）
    func frame(for behaviorId: String) -> String {
        let raw = behaviors[behaviorId]?.frame ?? behaviorId
        return frameAliases[raw] ?? raw
    }

    func line(for behaviorId: String) -> String {
        behaviors[behaviorId]?.line ?? ""
    }

    /// 当前时段对应的随机行为池（与 Android 的 BodyClock + scenePlans 对齐）
    func plan(for phaseId: String) -> [String] {
        scenePlans[phaseId] ?? scenePlans["default"] ?? ["think"]
    }
}
