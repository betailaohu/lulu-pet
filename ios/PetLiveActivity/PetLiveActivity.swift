import ActivityKit
import WidgetKit
import SwiftUI

struct PetActivityAttributes: ActivityAttributes {
    struct ContentState: Codable, Hashable {
        var statusText: String
        var frameId: String
        var satiety: Double
    }

    var name: String = "水豚噜噜"
}

/// Live Activity 的 UI 必须由 Widget Extension 提供，所以这个文件被 App 和 Widget 两个 target 一起编译。
@available(iOS 16.1, *)
struct LuluLiveActivity: Widget {
    var body: some WidgetConfiguration {
        ActivityConfiguration(for: PetActivityAttributes.self) { context in
            lockScreenView(context: context)
                .padding(12)
                .activityBackgroundTint(Color(uiColor: .systemBackground))
        } dynamicIsland: { context in
            DynamicIsland {
                DynamicIslandExpandedRegion(.leading) {
                    petImage(context.state.frameId).frame(width: 40, height: 40)
                }
                DynamicIslandExpandedRegion(.trailing) {
                    Text("\(Int(context.state.satiety))").font(.caption)
                }
                DynamicIslandExpandedRegion(.center) {
                    Text(context.state.statusText).font(.caption2).lineLimit(1)
                }
                DynamicIslandExpandedRegion(.bottom) {
                    Text("噜噜在这里陪你")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
            } compactLeading: {
                Image(systemName: "leaf.fill")
            } compactTrailing: {
                Text("\(Int(context.state.satiety))").font(.caption2)
            } minimal: {
                Image(systemName: "leaf.fill")
            }
        }
    }

    private func petImage(_ frameId: String) -> some View {
        Group {
            if let ui = UIImage(named: "frame-\(frameId)") {
                Image(uiImage: ui).resizable().scaledToFit()
            } else {
                Image(systemName: "leaf.fill").resizable().scaledToFit()
            }
        }
    }

    private func lockScreenView(
        context: ActivityViewContext<PetActivityAttributes>
    ) -> some View {
        HStack(spacing: 12) {
            petImage(context.state.frameId).frame(width: 44, height: 44)
            VStack(alignment: .leading, spacing: 2) {
                Text(context.attributes.name).font(.caption).bold()
                Text(context.state.statusText).font(.footnote)
            }
            Spacer()
        }
    }
}

/// 由主 App 的 PetState.publish() 调用。
/// Apple 把 Live Activity 定义为「进行中的临时事件」，这里设 30 分钟 staleDate，
/// 避免做成一个永远不结束的常驻活动（审核风险）。
@available(iOS 16.1, *)
enum PetLiveActivityManager {
    static func startOrUpdate(snapshot: AppGroup.Snapshot) {
        guard ActivityAuthorizationInfo().areActivitiesEnabled else { return }

        let state = PetActivityAttributes.ContentState(
            statusText: snapshot.statusText,
            frameId: snapshot.frameId,
            satiety: snapshot.satiety
        )
        let stale = Calendar.current.date(byAdding: .minute, value: 30, to: Date())
        let content = ActivityContent(state: state, staleDate: stale)

        if let activity = Activity<PetActivityAttributes>.activities.first {
            Task { await activity.update(content) }
        } else {
            let attributes = PetActivityAttributes(name: "水豚噜噜")
            _ = try? Activity.request(
                attributes: attributes,
                content: content,
                pushType: nil
            )
        }
    }

    static func end() {
        Task {
            for activity in Activity<PetActivityAttributes>.activities {
                await activity.end(nil, dismissalPolicy: .immediate)
            }
        }
    }
}
