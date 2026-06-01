import SwiftUI
import AppKit
import AVKit

/// Root composition: full-bleed video with overlaid HUD/deck, optional sidebar
/// and help slide-out. All keyboard input flows through the focusable root.
struct RootView: View {
    @EnvironmentObject var state: ReviewerState
    @EnvironmentObject var playback: PlaybackController
    @EnvironmentObject var viewport: TimelineViewport

    @State private var showSidebar: Bool = true
    @State private var showHelp: Bool = false
    @State private var showReviewQueue: Bool = false
    @State private var hudVisible: Bool = true
    @State private var hudFadeTask: Task<Void, Never>?

    var body: some View {
        HStack(spacing: 0) {
            if showSidebar {
                SessionSidebar()
                    .frame(width: 240)
                    .transition(.move(edge: .leading))
                Divider()
            }
            mainStage
            if showReviewQueue {
                Divider()
                ReviewQueuePanel(onClose: { withAnimation { showReviewQueue = false } })
                    .frame(width: 360)
                    .transition(.move(edge: .trailing))
            }
        }
        .overlay(alignment: .trailing) {
            if showHelp {
                HelpPanel(onClose: { withAnimation { showHelp = false } })
                    .frame(width: 360)
                    .transition(.move(edge: .trailing))
            }
        }
        .background(Color(nsColor: .windowBackgroundColor))
        .animation(.easeInOut(duration: 0.18), value: showSidebar)
        .animation(.easeInOut(duration: 0.18), value: showHelp)
        .animation(.easeInOut(duration: 0.18), value: showReviewQueue)
        .onReceive(NotificationCenter.default.publisher(for: .toggleSidebar)) { _ in
            showSidebar.toggle()
        }
        .onReceive(NotificationCenter.default.publisher(for: .toggleHelp)) { _ in
            showHelp.toggle()
        }
        .onReceive(NotificationCenter.default.publisher(for: .pickWorkspace)) { _ in
            pickWorkspaceRoot()
        }
        .onReceive(NotificationCenter.default.publisher(for: .toggleReviewQueue)) { _ in
            withAnimation { showReviewQueue.toggle() }
        }
        .onChange(of: playback.isPlaying) { _, playing in
            if playing {
                scheduleHUDFade()
                viewport.snapToPlayhead(playback.currentTime, duration: max(playback.duration, 1))
            } else {
                revealHUD()
            }
        }
        .onChange(of: state.selectedSession?.id) { _, _ in
            loadEffectiveVideo(preserveTime: false)
        }
        .onChange(of: state.useAnnotatedVideo) { _, _ in
            loadEffectiveVideo(preserveTime: true)
        }
        .onChange(of: state.selectedChewID) { _, _ in applySelectionBounds() }
        .onChange(of: state.loopSelectedChew) { _, _ in applySelectionBounds() }
    }

    // MARK: - Main stage

    @ViewBuilder
    private var mainStage: some View {
        if state.workspaceRoot == nil {
            workspacePrompt
        } else if state.selectedSession == nil {
            ContentUnavailableView(
                "Pick a session",
                systemImage: "video.circle",
                description: Text("Choose a session in the sidebar to start labeling chews.")
            )
        } else if state.selectedSession?.videoURL == nil {
            ContentUnavailableView(
                "No video for this session",
                systemImage: "video.slash",
                description: Text("Place an .mp4 / .mov in the session’s raw folder.")
            )
        } else {
            videoStage
        }
    }

    private var workspacePrompt: some View {
        VStack(spacing: 14) {
            Text("ChewSense Cycle Reviewer").font(.title2).bold()
            Text("Choose the ChewSense project root to discover sessions.")
                .multilineTextAlignment(.center)
                .foregroundStyle(.secondary)
                .frame(maxWidth: 520)
            Button("Choose workspace…") { pickWorkspaceRoot() }
                .buttonStyle(.borderedProminent)
        }
        .padding()
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private var videoStage: some View {
        ZStack {
            VideoSurface()
                .background(Color.black)
                .onTapGesture { revealHUD(); scheduleHUDFade() }
                .onContinuousHover { _ in revealHUD(); scheduleHUDFade() }

            VStack {
                if hudVisible {
                    HUDTop(toggleSidebar: { showSidebar.toggle() },
                           toggleHelp: { showHelp.toggle() },
                           toggleReviewQueue: { showReviewQueue.toggle() })
                        .padding(.horizontal, 12)
                        .padding(.top, 10)
                        .transition(.opacity)
                }
                Spacer()
                if state.selectedChew != nil {
                    CycleShapeChart()
                        .padding(.horizontal, 12)
                        .padding(.bottom, 6)
                        .transition(.opacity)
                }
                BottomDeck()
                    .padding(.horizontal, 12)
                    .padding(.bottom, 12)
            }

            KeyCaptureView(handler: handleKey)
                .frame(width: 0, height: 0)
        }
        .animation(.easeInOut(duration: 0.15), value: hudVisible)
    }

    // MARK: - Helpers

    private func pickWorkspaceRoot() {
        let panel = NSOpenPanel()
        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.allowsMultipleSelection = false
        panel.prompt = "Select ChewSense root"
        if panel.runModal() == .OK, let url = panel.url {
            state.setWorkspaceRoot(url)
        }
    }

    private func revealHUD() {
        hudFadeTask?.cancel()
        if !hudVisible { hudVisible = true }
    }

    private func scheduleHUDFade() {
        hudFadeTask?.cancel()
        guard playback.isPlaying else { return }
        hudFadeTask = Task { @MainActor in
            try? await Task.sleep(nanoseconds: 2_500_000_000)
            if !Task.isCancelled, playback.isPlaying { hudVisible = false }
        }
    }

    private func applySelectionBounds() {
        // Cycle-selected state: when a chew is selected, bound playback so
        // pressing play starts at the cycle's start and ends at its end.
        // The loop toggle (R) optionally restarts at the end instead of pausing.
        guard let chew = state.selectedChew else {
            playback.clearLoop()
            return
        }
        playback.setLoop(start: chew.startTS, end: chew.endTS, enabled: state.loopSelectedChew)
    }

    /// Resolves the URL to feed AVPlayer based on the current Raw/Annotated
    /// toggle, falling back to the raw video when the annotated reference is
    /// missing. When `preserveTime` is true the playhead is restored after
    /// the swap so the reviewer can compare frames at the same timestamp.
    private func loadEffectiveVideo(preserveTime: Bool) {
        guard let session = state.selectedSession else { return }
        let url: URL? = (state.useAnnotatedVideo ? session.annotatedVideoURL : nil)
            ?? session.videoURL
        guard let url else { return }
        let savedTime = preserveTime ? playback.currentTime : 0
        playback.load(url: url)
        if preserveTime, savedTime > 0 {
            playback.seek(to: savedTime)
        }
    }

    private func playOrPauseFromSelectedCycleStart() {
        if playback.isPlaying {
            playback.pause()
            return
        }
        if let chew = state.selectedChew {
            playback.setLoop(start: chew.startTS, end: chew.endTS, enabled: state.loopSelectedChew)
            playback.playWithinCycle(start: chew.startTS, end: chew.endTS)
        } else {
            playback.play()
        }
    }

    // MARK: - Key handler

    private func handleKey(_ event: NSEvent, held: Set<String>) -> NSEvent? {
        guard state.selectedSession != nil else { return event }
        let chars = event.charactersIgnoringModifiers ?? ""
        let mods = event.modifierFlags.intersection(.deviceIndependentFlagsMask)
        let plain = mods.subtracting(.numericPad).isEmpty
        let shift = mods == .shift
        let option = mods == .option

        // S/P/E + ←/→ chord: nudge that marker on the selected chew.
        // Holding s/p/e suppresses their normal key actions while down.
        let chordMarker: ChewMarker? = {
            if held.contains("s") { return .start }
            if held.contains("p") { return .peak }
            if held.contains("e") { return .end }
            return nil
        }()
        if let marker = chordMarker, (event.keyCode == 123 || event.keyCode == 124) {
            let frames: Double = shift ? 5.0 : 1.0
            let dir: Double = (event.keyCode == 124) ? 1.0 : -1.0
            let delta = dir * frames / 30.0
            if let chew = state.selectedChew {
                let target = chew.timestamp(for: marker) + delta
                state.updateMarker(chewID: chew.id, marker: marker, to: target, recordUndo: true)
                if let updated = state.chews.first(where: { $0.id == chew.id }) {
                    playback.seek(to: updated.timestamp(for: marker))
                }
            }
            return nil
        }
        // While a chord key is held, swallow plain s/p/e keystrokes so they
        // don't trigger their unrelated actions (e.g. p = previous chew).
        if !held.isEmpty, plain, ["s", "p", "e"].contains(chars.lowercased()) {
            return nil
        }

        switch (chars, mods) {
        case (" ", _) where plain:
            playOrPauseFromSelectedCycleStart(); return nil
        case ("1", _) where plain:
            setMarkerAtPlayhead(.start); return nil
        case ("2", _) where plain:
            setMarkerAtPlayhead(.peak); return nil
        case ("3", _) where plain:
            setMarkerAtPlayhead(.end); return nil
        case ("a", _), ("A", _):
            quickAddAtPlayhead(); return nil
        case ("d", _), ("D", _):
            state.deleteSelectedOrAt(videoTime: playback.currentTime); return nil
        case ("n", _), ("N", _):
            if let c = state.selectNextChew() { playback.seek(to: c.startTS) }; return nil
        case ("p", _), ("P", _):
            if let c = state.selectPreviousChew() { playback.seek(to: c.startTS) }; return nil
        case ("[", _) where plain:
            if let c = state.selectedChew { playback.seek(to: c.startTS) }; return nil
        case ("]", _) where plain:
            if let c = state.selectedChew { playback.seek(to: c.endTS) }; return nil
        case ("j", _), ("J", _):
            playback.skip(by: -1.0); return nil
        case ("l", _), ("L", _):
            playback.skip(by: 1.0); return nil
        case ("k", _), ("K", _):
            playOrPauseFromSelectedCycleStart(); return nil
        case ("r", _), ("R", _):
            state.loopSelectedChew.toggle(); return nil
        case ("o", _), ("O", _):
            if state.selectedSession?.annotatedVideoURL != nil {
                state.useAnnotatedVideo.toggle()
            } else {
                state.statusMessage = "No annotated_video.mp4 for this session"
            }
            return nil
        case ("=", _), ("+", _):
            viewport.zoomIn(pivot: playback.currentTime); return nil
        case ("-", _), ("_", _):
            viewport.zoomOut(pivot: playback.currentTime); return nil
        case ("0", _) where plain:
            viewport.fit(); return nil
        case ("f", _), ("F", _):
            if let c = state.selectedChew {
                viewport.focus(on: c, duration: max(playback.duration, 1))
            }
            return nil
        case (",", _) where plain:
            if let m = state.previousMarker(before: playback.currentTime) {
                playback.seek(to: m.time)
                state.selectChew(id: m.chewID)
                state.lastTouchedMarker = m.marker
            }
            return nil
        case (".", _) where plain:
            if let m = state.nextMarker(after: playback.currentTime) {
                playback.seek(to: m.time)
                state.selectChew(id: m.chewID)
                state.lastTouchedMarker = m.marker
            }
            return nil
        case ("v", _) where plain:
            if let next = state.verifyAndAdvance() {
                playback.seek(to: next.startTS)
                viewport.focus(on: next, duration: max(playback.duration, 1))
            }
            return nil
        case ("V", _):
            if let id = state.selectedChewID { state.toggleChewVerified(id: id) }
            return nil
        case ("m", _), ("M", _):
            showReviewQueue.toggle(); return nil
        default: break
        }

        // Arrow keys: ← → step, ⇧ skip, ⌥ nudge marker
        switch event.keyCode {
        case 123: // left
            if option { state.nudgeLastTouchedMarker(by: -1.0/30.0); seekToLastMarker() }
            else if shift { playback.skip(by: -0.25) }
            else { playback.skip(by: -1.0/30.0) }
            return nil
        case 124: // right
            if option { state.nudgeLastTouchedMarker(by: 1.0/30.0); seekToLastMarker() }
            else if shift { playback.skip(by: 0.25) }
            else { playback.skip(by: 1.0/30.0) }
            return nil
        case 51, 117: // delete, fwd-delete
            state.deleteSelectedOrAt(videoTime: playback.currentTime); return nil
        case 115: // home
            playback.seekToStart(); return nil
        case 119: // end
            playback.seekToEnd(); return nil
        default: break
        }
        return event
    }

    private func setMarkerAtPlayhead(_ marker: ChewMarker) {
        let t = playback.currentTime
        if let chew = state.selectedChew {
            state.updateMarker(chewID: chew.id, marker: marker, to: t)
            state.lastTouchedMarker = marker
        } else {
            // No selection — quick-add a chew if space allows.
            quickAddAtPlayhead()
        }
    }

    private func quickAddAtPlayhead() {
        let t = playback.currentTime
        let half = 0.21
        state.addChew(start: max(0, t - half), end: t + half, peak: t)
    }

    private func seekToLastMarker() {
        if let c = state.selectedChew {
            playback.seek(to: c.timestamp(for: state.lastTouchedMarker))
        }
    }
}

// MARK: - Video surface (custom AVPlayerLayer-backed view)

private struct VideoSurface: NSViewRepresentable {
    @EnvironmentObject var playback: PlaybackController

    func makeNSView(context: Context) -> AVPlayerView {
        let v = AVPlayerView()
        v.controlsStyle = .none
        v.showsFullScreenToggleButton = false
        v.player = playback.player
        v.videoGravity = .resizeAspect
        return v
    }

    func updateNSView(_ nsView: AVPlayerView, context: Context) {
        if nsView.player !== playback.player {
            nsView.player = playback.player
        }
    }
}

// MARK: - Key capture (focusable transparent NSView for first-responder)

private struct KeyCaptureView: NSViewRepresentable {
    let handler: (NSEvent, Set<String>) -> NSEvent?

    func makeNSView(context: Context) -> KeyCaptureNSView {
        let v = KeyCaptureNSView()
        v.handler = handler
        DispatchQueue.main.async { v.window?.makeFirstResponder(v) }
        return v
    }

    func updateNSView(_ nsView: KeyCaptureNSView, context: Context) {
        nsView.handler = handler
        if nsView.window?.firstResponder !== nsView {
            DispatchQueue.main.async { nsView.window?.makeFirstResponder(nsView) }
        }
    }
}

final class KeyCaptureNSView: NSView {
    var handler: ((NSEvent, Set<String>) -> NSEvent?)?
    /// Currently-held marker chord keys (s/p/e). Read by the handler to
    /// decide whether to treat ←/→ as a marker nudge.
    private(set) var heldChordKeys: Set<String> = []
    private var resignObserver: NSObjectProtocol?

    override var acceptsFirstResponder: Bool { true }
    override func becomeFirstResponder() -> Bool { true }

    override func viewDidMoveToWindow() {
        super.viewDidMoveToWindow()
        if let obs = resignObserver {
            NotificationCenter.default.removeObserver(obs)
            resignObserver = nil
        }
        if let win = window {
            // Clear stuck chord keys when the app loses key window focus.
            resignObserver = NotificationCenter.default.addObserver(
                forName: NSWindow.didResignKeyNotification, object: win, queue: .main
            ) { [weak self] _ in
                self?.heldChordKeys.removeAll()
            }
        }
    }

    override func keyDown(with event: NSEvent) {
        // Skip if a text field is the first responder.
        if let resp = window?.firstResponder, resp is NSText {
            super.keyDown(with: event); return
        }
        let chars = (event.charactersIgnoringModifiers ?? "").lowercased()
        let modsClean = event.modifierFlags
            .intersection(.deviceIndependentFlagsMask)
            .subtracting([.shift, .numericPad])
        if !event.isARepeat, modsClean.isEmpty, ["s", "p", "e"].contains(chars) {
            heldChordKeys.insert(chars)
        }
        if handler?(event, heldChordKeys) == nil { return }
        super.keyDown(with: event)
    }

    override func keyUp(with event: NSEvent) {
        let chars = (event.charactersIgnoringModifiers ?? "").lowercased()
        if ["s", "p", "e"].contains(chars) {
            heldChordKeys.remove(chars)
        }
        super.keyUp(with: event)
    }

    deinit {
        if let obs = resignObserver {
            NotificationCenter.default.removeObserver(obs)
        }
    }
}
