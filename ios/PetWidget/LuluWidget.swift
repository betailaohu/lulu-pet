import WidgetKit
import SwiftUI
import UIKit

struct LuluEntry: TimelineEntry {
    let date: Date
    let snapshot: AppGroup.Snapshot
}

struct PetTimelineProvider: TimelineProvider {
    func placeholder(in context: Context) -> LuluEntry {
        LuluEntry(date: Date(), snapshot: .placeholder())
    }

    func getSnapshot(in context: Context, completion: @escaping (LuluEntry) -> Void) {
        completion(LuluEntry(date: Date(), snapshot: AppGroup.read() ?? .placeholder()))
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<LuluEntry>) -> Void) {
        let snapshot = AppGroup.read() ?? .placeholder()
        let entry = LuluEntry(date: Date(), snapshot: snapshot)
        // 15 分钟只是「最早再次请求」，实际刷新由系统按预算调度，可能延后
        let next = Calendar.current.date(byAdding: .minute, value: 15, to: Date()) ?? Date()
        completion(Timeline(entries: [entry], policy: .after(next)))
    }
}

struct LuluWidgetView: View {
    @Environment(\.widgetFamily) private var family
    let entry: LuluEntry

    var body: some View {
        Group {
            switch family {
            case .systemSmall:
                small
            case .accessoryCircular:
                circular
            case .accessoryInline:
                inline
            case .accessoryRectangular:
                rectangular
            default:
                medium
            }
        }
        .padding(10)
        // iOS 17 起小组件必须用 containerBackground，否则系统会报
        // "Please adopt containerBackground API" 并且背景渲染异常。
        .containerBackground(for: .widget) {
            Color(uiColor: .systemBackground)
        }
    }

    private var image: some View {
        Group {
            if let ui = UIImage(named: "frame-\(entry.snapshot.frameId)") {
                Image(uiImage: ui).resizable().scaledToFit()
            } else {
                Image(systemName: "leaf.fill")
                    .resizable().scaledToFit()
                    .foregroundStyle(.brown)
            }
        }
    }

    private var small: some View {
        VStack(spacing: 4) {
            image.frame(width: 82, height: 82)
            Text(entry.snapshot.statusText)
                .font(.caption2)
                .lineLimit(1)
                .minimumScaleFactor(0.7)
        }
    }

    private var medium: some View {
        HStack(spacing: 14) {
            image.frame(width: 96, height: 96)
            VStack(alignment: .leading, spacing: 6) {
                Text("水豚噜噜").font(.headline)
                Text(entry.snapshot.statusText).font(.footnote)
                bar("饱食度", entry.snapshot.satiety, .orange)
                bar("心情", entry.snapshot.mood, .pink)
            }
        }
    }

    private func bar(_ title: String, _ value: Double, _ tint: Color) -> some View {
        HStack(spacing: 6) {
            Text(title).font(.caption2).frame(width: 42, alignment: .leading)
            ProgressView(value: min(max(value / 100, 0), 1)).tint(tint)
        }
    }

    private var rectangular: some View {
        HStack(spacing: 8) {
            image.frame(width: 30, height: 30)
            VStack(alignment: .leading) {
                Text("噜噜").font(.caption2).bold()
                Text(entry.snapshot.statusText).font(.caption2).lineLimit(1)
            }
        }
    }

    private var circular: some View {
        ZStack {
            AccessoryWidgetBackground()
            ProgressView(value: min(max(entry.snapshot.satiety / 100, 0), 1))
                .progressViewStyle(.circular)
                .tint(.brown)
        }
    }

    private var inline: some View {
        Text("噜噜 · \(entry.snapshot.statusText)")
    }
}

struct LuluWidget: Widget {
    let kind = "LuluWidget"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: PetTimelineProvider()) { entry in
            LuluWidgetView(entry: entry)
        }
        .configurationDisplayName("水豚噜噜")
        .description("瞄一眼噜噜现在怎么样")
        .supportedFamilies([
            .systemSmall, .systemMedium,
            .accessoryCircular, .accessoryRectangular, .accessoryInline
        ])
    }
}

/// Widget Extension 入口：小组件 + Live Activity 注册在同一个 bundle。
@main
struct LuluWidgetBundle: WidgetBundle {
    var body: some Widget {
        LuluWidget()
        LuluLiveActivity()
    }
}
