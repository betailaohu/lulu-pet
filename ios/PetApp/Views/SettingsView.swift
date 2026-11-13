import SwiftUI

/// 设置页：把三条养成数值摊开给人看，并给出小组件/灵动岛的状态与手动操作。
struct SettingsView: View {
    @EnvironmentObject private var state: PetState
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            Form {
                Section("养成数值") {
                    statRow("饱食度", state.satiety, .orange, "低于 30 会喊饿")
                    statRow("心情", state.mood, .pink, "低于 25 会低落")
                    statRow("亲密度", state.affinity, .brown, "摸头 +1，每日上限 20")
                }

                Section("小组件与灵动岛") {
                    LabeledContent("共享通道") {
                        Text(AppGroup.isSharedStoreAvailable ? "已连接" : "不可用")
                            .foregroundStyle(AppGroup.isSharedStoreAvailable ? Color.green : Color.secondary)
                    }
                    if !AppGroup.isSharedStoreAvailable {
                        Text("免费 Apple ID 侧载时拿不到 App Group 权限，桌面小组件会一直显示默认快照；主 App 内一切正常。")
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                    }
                    Button("立即刷新小组件") { state.publish() }
                    Button("结束灵动岛活动") { state.endLiveActivity() }
                }

                Section("重置") {
                    Button("数值恢复初始值", role: .destructive) { state.reset() }
                }

                Section("关于") {
                    LabeledContent("版本", value: "0.1.0")
                    Text("非官方同人作品，不接广告、不做内购。形象版权归原权利方，本项目仅作个人学习使用。")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
            }
            .navigationTitle("设置")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("完成") { dismiss() }
                }
            }
        }
    }

    private func statRow(_ title: String, _ value: Double, _ tint: Color, _ hint: String) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text(title)
                Spacer()
                Text("\(Int(value)) / 100").monospacedDigit().foregroundStyle(.secondary)
            }
            ProgressView(value: min(max(value / 100, 0), 1)).tint(tint)
            Text(hint).font(.caption2).foregroundStyle(.secondary)
        }
    }
}
