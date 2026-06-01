import SwiftUI

@main
struct ChewSenseCycleReviewerApp: App {
    @StateObject private var state = ReviewerState()
    @StateObject private var playback = PlaybackController()
    @StateObject private var viewport = TimelineViewport()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(state)
                .environmentObject(playback)
                .environmentObject(viewport)
                .frame(minWidth: 980, minHeight: 640)
        }
        .windowToolbarStyle(.unifiedCompact)
        .commands {
            CommandGroup(replacing: .newItem) {}
            CommandGroup(replacing: .undoRedo) {
                Button("Undo") { state.undo() }
                    .keyboardShortcut("z", modifiers: [.command])
                    .disabled(!state.canUndo)
                Button("Redo") { state.redo() }
                    .keyboardShortcut("z", modifiers: [.command, .shift])
                    .disabled(!state.canRedo)
            }
            CommandGroup(replacing: .saveItem) {
                Button("Save Overrides") { state.saveOverrides() }
                    .keyboardShortcut("s", modifiers: [.command])
                    .disabled(state.selectedSession == nil)
            }
            CommandGroup(after: .sidebar) {
                Button("Toggle Sidebar") {
                    NotificationCenter.default.post(name: .toggleSidebar, object: nil)
                }
                .keyboardShortcut("1", modifiers: [.command])
                Button("Toggle Help") {
                    NotificationCenter.default.post(name: .toggleHelp, object: nil)
                }
                .keyboardShortcut("/", modifiers: [.command])
                Button("Open Review Queue") {
                    NotificationCenter.default.post(name: .toggleReviewQueue, object: nil)
                }
                .keyboardShortcut("m", modifiers: [.command])
            }
            CommandGroup(after: .appInfo) {
                Button("Open Workspace…") {
                    NotificationCenter.default.post(name: .pickWorkspace, object: nil)
                }
                .keyboardShortcut("o", modifiers: [.command])
            }
        }
    }
}

extension Notification.Name {
    static let toggleSidebar = Notification.Name("ChewSense.toggleSidebar")
    static let toggleHelp = Notification.Name("ChewSense.toggleHelp")
    static let pickWorkspace = Notification.Name("ChewSense.pickWorkspace")
    static let toggleReviewQueue = Notification.Name("ChewSense.toggleReviewQueue")
}
