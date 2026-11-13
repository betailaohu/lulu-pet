import SwiftUI
import Combine

@main
struct LuluApp: App {
    @StateObject private var petState = PetState()
    @Environment(\.scenePhase) private var scenePhase
    private let refreshTimer = Timer.publish(every: 60, on: .main, in: .common).autoconnect()

    var body: some Scene {
        WindowGroup {
            PetView()
                .environmentObject(petState)
                .onChange(of: scenePhase) { phase in
                    if phase == .active { petState.refresh() }
                }
                .onReceive(refreshTimer) { _ in
                    if scenePhase == .active { petState.refresh() }
                }
        }
    }
}
