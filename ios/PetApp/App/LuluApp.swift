import SwiftUI

@main
struct LuluApp: App {
    @StateObject private var petState = PetState()

    var body: some Scene {
        WindowGroup {
            PetView()
                .environmentObject(petState)
        }
    }
}
