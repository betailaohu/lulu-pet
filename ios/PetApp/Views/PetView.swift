import SwiftUI

/// iOS 上唯一能「动起来」的地方：状态立绘切换 + 呼吸位移 + 摸头/喂食互动。
/// 小组件和灵动岛只展示静态快照，不要在这里设计需要持续刷新的东西。
struct PetView: View {
    @EnvironmentObject private var state: PetState
    @State private var breathe = false
    @State private var showSettings = false

    var body: some View {
        VStack(spacing: 18) {
            Spacer(minLength: 12)

            ZStack(alignment: .top) {
                petImage
                    .offset(y: breathe ? -6 : 6)
                    .animation(
                        .easeInOut(duration: 2.4).repeatForever(autoreverses: true),
                        value: breathe
                    )
                    .onAppear { breathe = true }
                    .onTapGesture { state.pat() }

                if let bubble = state.bubble {
                    Text(bubble)
                        .font(.footnote)
                        .padding(10)
                        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 12))
                        .offset(y: -36)
                        .transition(.opacity)
                }
            }
            .frame(height: 280)

            Text(state.statusText)
                .font(.headline)

            HStack(spacing: 22) {
                statBar("饱食度", state.satiety, .orange)
                statBar("心情", state.mood, .pink)
                statBar("亲密度", state.affinity, .brown)
            }

            HStack(spacing: 12) {
                Button {
                    state.feed()
                } label: {
                    Label("喂一把草", systemImage: "leaf.fill")
                }
                .buttonStyle(.borderedProminent)
                .tint(.brown)

                Button {
                    state.play(state.urgentBehavior() ?? "wonder")
                } label: {
                    Label("逗一下", systemImage: "hand.tap")
                }
                .buttonStyle(.bordered)
            }

            Text("小组件与灵动岛在桌面/锁屏上陪伴你，点这里可以摸摸头")
                .font(.caption2)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)

            Spacer(minLength: 12)
        }
        .padding()
        .background(Color(uiColor: .systemGroupedBackground))
        .overlay(alignment: .topTrailing) {
            Button {
                showSettings = true
            } label: {
                Image(systemName: "gearshape")
                    .font(.title3)
                    .padding(8)
            }
            .padding(.top, 4)
            .padding(.trailing, 4)
        }
        .sheet(isPresented: $showSettings) {
            SettingsView().environmentObject(state)
        }
    }

    private var petImage: some View {
        Group {
            if let uiImage = UIImage(named: "frame-\(state.frameId)") {
                Image(uiImage: uiImage)
                    .resizable()
                    .scaledToFit()
                    .frame(width: 260, height: 260)
            } else {
                Image(systemName: "photo")
                    .resizable()
                    .scaledToFit()
                    .frame(width: 120, height: 120)
                    .foregroundStyle(.secondary)
            }
        }
    }

    private func statBar(_ title: String, _ value: Double, _ tint: Color) -> some View {
        VStack(spacing: 4) {
            Text(title).font(.caption2).foregroundStyle(.secondary)
            ProgressView(value: min(max(value / 100, 0), 1))
                .tint(tint)
                .frame(width: 82)
            Text("\(Int(value))").font(.caption2)
        }
    }
}
