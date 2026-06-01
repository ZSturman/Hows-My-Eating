import SwiftUI

/// Review Queue: a focused side panel for watching each chew end-to-end and
/// confirming Start / Peak / End. The current chew loops in the main video
/// stage (clip-cinema mode) while this panel surfaces marker-level controls.
struct ReviewQueuePanel: View {
    @EnvironmentObject var state: ReviewerState
    @EnvironmentObject var playback: PlaybackController
    @EnvironmentObject var viewport: TimelineViewport

    let onClose: () -> Void

    @State private var queueIndex: Int = 0
    /// Chew IDs in queue order (snapshot at sheet open so deletions don't reshuffle).
    @State private var queue: [String] = []
    /// Show only unverified chews when true.
    @State private var unverifiedOnly: Bool = true
    @State private var showList: Bool = false

    var body: some View {
        VStack(spacing: 0) {
            header
            Divider()
            ScrollView {
                VStack(alignment: .leading, spacing: 12) {
                    progressBar
                    detailPane
                    if showList {
                        Divider()
                        queueList.frame(minHeight: 180, maxHeight: 260)
                    }
                }
                .padding(12)
            }
        }
        .frame(maxHeight: .infinity)
        .background(Color(nsColor: .windowBackgroundColor))
        .onAppear {
            rebuildQueue(reset: true)
        }
        .onChange(of: unverifiedOnly) { _, _ in rebuildQueue(reset: true) }
        .onChange(of: state.chews.map(\.id)) { _, _ in rebuildQueue(reset: false) }
        .onDisappear {
            playback.clearLoop()
        }
    }

    private var header: some View {
        VStack(spacing: 6) {
            HStack(spacing: 8) {
                Image(systemName: "play.rectangle.on.rectangle.fill")
                    .font(.title3).foregroundStyle(.tint)
                Text("Review Queue").font(.headline)
                Spacer()
                Button(action: onClose) { Image(systemName: "xmark") }
                    .buttonStyle(.plain)
                    .help("Close (M)")
            }
            HStack {
                Toggle("Unverified only", isOn: $unverifiedOnly)
                    .toggleStyle(.switch)
                    .controlSize(.small)
                Spacer()
                Button {
                    showList.toggle()
                } label: {
                    Image(systemName: showList ? "list.bullet.indent" : "list.bullet")
                }
                .buttonStyle(.plain)
                .help("Show full queue")
                Text("\(state.verifiedCount) / \(state.chews.count)")
                    .font(.system(.caption, design: .monospaced).monospacedDigit())
                    .foregroundStyle(.secondary)
            }
        }
        .padding(12)
    }

    // MARK: - Queue list

    private var queueList: some View {
        List(selection: Binding(
            get: { currentChewID },
            set: { id in
                if let id, let i = queue.firstIndex(of: id) {
                    queueIndex = i
                    cueCurrentChew()
                }
            }
        )) {
            ForEach(Array(queue.enumerated()), id: \.element) { (idx, chewID) in
                if let c = state.chews.first(where: { $0.id == chewID }) {
                    HStack {
                        Image(systemName: state.isVerified(id: chewID) ? "checkmark.seal.fill" : "circle")
                            .foregroundStyle(state.isVerified(id: chewID) ? .green : .secondary)
                        VStack(alignment: .leading, spacing: 2) {
                            Text(c.id).font(.system(.caption, design: .monospaced))
                            Text(String(format: "%.2fs · %.0fms", c.startTS, c.duration * 1000))
                                .font(.caption2).foregroundStyle(.secondary)
                        }
                        Spacer()
                        Text("\(idx + 1)")
                            .font(.caption2.monospacedDigit())
                            .foregroundStyle(.secondary)
                    }
                    .tag(chewID)
                }
            }
        }
        .listStyle(.bordered)
    }

    // MARK: - Detail pane

    @ViewBuilder
    private var detailPane: some View {
        if let chew = currentChew {
            VStack(alignment: .leading, spacing: 10) {
                HStack {
                    Text(chew.id).font(.system(.title3, design: .monospaced))
                    if state.isVerified(id: chew.id) {
                        Image(systemName: "checkmark.seal.fill").foregroundStyle(.green)
                    }
                    Spacer()
                }
                if let seg = state.eatingSegment(enclosing: chew) {
                    HStack(spacing: 6) {
                        Image(systemName: "fork.knife")
                            .foregroundStyle(.blue)
                        Text("Eating \(String(format: "%.2fs–%.2fs", seg.startTS, seg.endTS))")
                            .font(.caption.monospacedDigit())
                            .foregroundStyle(.secondary)
                        Text("· \(String(format: "%.1fs", seg.duration))")
                            .font(.caption.monospacedDigit())
                            .foregroundStyle(.secondary)
                    }
                }
                Grid(alignment: .leading, horizontalSpacing: 12, verticalSpacing: 4) {
                    markerRow(.start, time: chew.startTS, color: .green, symbol: "play.fill")
                    markerRow(.peak,  time: chew.peakTS,  color: .yellow, symbol: "diamond.fill")
                    markerRow(.end,   time: chew.endTS,   color: .red, symbol: "play.fill")
                }
                .font(.system(.caption, design: .monospaced))

                actionButtons
                hintFooter
            }
            .padding(10)
            .background(Color.gray.opacity(0.08), in: RoundedRectangle(cornerRadius: 8))
        } else {
            VStack(spacing: 8) {
                Image(systemName: "checkmark.seal.fill").font(.largeTitle).foregroundStyle(.green)
                Text("Queue complete").font(.headline)
                Text("Toggle 'Unverified only' off to revisit verified chews.")
                    .font(.caption).foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
            }
            .padding()
            .frame(maxWidth: .infinity)
        }
    }

    private var progressBar: some View {
        HStack(spacing: 8) {
            Text("\(queueIndex + 1) of \(queue.count)")
                .font(.system(.callout, design: .monospaced).monospacedDigit())
            ProgressView(value: Double(queueIndex + 1), total: Double(max(1, queue.count)))
        }
    }

    private func markerRow(_ marker: ChewMarker, time: Double, color: Color, symbol: String) -> some View {
        GridRow {
            HStack(spacing: 6) {
                Image(systemName: symbol)
                    .foregroundStyle(color)
                    .rotationEffect(.degrees(marker == .end ? 180 : 0))
                Text(marker.displayName)
            }
            Text(String(format: "%.3fs", time))
            HStack(spacing: 4) {
                Button { nudge(marker, by: -1.0/30.0) } label: { Image(systemName: "chevron.left") }
                    .buttonStyle(.borderless)
                Button { nudge(marker, by: 1.0/30.0) } label: { Image(systemName: "chevron.right") }
                    .buttonStyle(.borderless)
                Button { playback.seek(to: time) } label: { Image(systemName: "scope") }
                    .buttonStyle(.borderless)
                    .help("Jump to \(marker.displayName.lowercased())")
            }
        }
    }

    private var actionButtons: some View {
        HStack(spacing: 8) {
            Button { previous() } label: {
                Image(systemName: "arrow.left")
            }
            .help("Previous")
            .disabled(queueIndex <= 0)

            Button { skipNext() } label: {
                Image(systemName: "arrow.right")
            }
            .help("Skip")

            Spacer()

            Button { playOrPauseCurrentChewFromStart() } label: {
                Image(systemName: playback.isPlaying ? "pause.fill" : "play.fill")
            }
            .help("Play / pause (Space)")

            Button {
                if let id = currentChewID {
                    state.toggleChewVerified(id: id)
                }
                next()
            } label: {
                Label(currentVerified ? "Unverify ›" : "Verify ›", systemImage: "checkmark.seal.fill")
            }
            .buttonStyle(.borderedProminent)
            .tint(.green)
            .help("Verify and advance (V)")
        }
    }

    private var hintFooter: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack(spacing: 10) {
                shortcut("V", "verify+next")
                shortcut("Space", "play/pause")
                shortcut("M", "close")
            }
            HStack(spacing: 10) {
                shortcut("S+←/→", "nudge start")
                shortcut("P+←/→", "nudge peak")
                shortcut("E+←/→", "nudge end")
            }
        }
        .font(.caption2)
        .foregroundStyle(.secondary)
    }

    private func shortcut(_ key: String, _ desc: String) -> some View {
        HStack(spacing: 4) {
            Text(key)
                .font(.system(.caption2, design: .monospaced))
                .padding(.horizontal, 4).padding(.vertical, 1)
                .background(Color.gray.opacity(0.2), in: RoundedRectangle(cornerRadius: 3))
            Text(desc)
        }
    }

    // MARK: - Actions

    private var currentChewID: String? { queue.indices.contains(queueIndex) ? queue[queueIndex] : nil }
    private var currentChew: ReviewChew? {
        guard let id = currentChewID else { return nil }
        return state.chews.first { $0.id == id }
    }
    private var currentVerified: Bool {
        guard let id = currentChewID else { return false }
        return state.isVerified(id: id)
    }

    private func rebuildQueue(reset: Bool) {
        let new = state.chews
            .filter { !unverifiedOnly || !state.isVerified(id: $0.id) }
            .map(\.id)
        queue = new
        if reset { queueIndex = 0 }
        if queueIndex >= queue.count { queueIndex = max(0, queue.count - 1) }
        cueCurrentChew()
    }

    private func next() {
        if queueIndex < queue.count - 1 {
            queueIndex += 1
            cueCurrentChew()
        } else if unverifiedOnly {
            rebuildQueue(reset: true)
        }
    }

    private func previous() {
        if queueIndex > 0 {
            queueIndex -= 1
            cueCurrentChew()
        }
    }

    private func skipNext() { next() }

    private func nudge(_ marker: ChewMarker, by delta: Double) {
        guard let id = currentChewID, let c = state.chews.first(where: { $0.id == id }) else { return }
        state.updateMarker(chewID: id, marker: marker, to: c.timestamp(for: marker) + delta)
        playback.seek(to: c.timestamp(for: marker) + delta)
    }

    private func setAtPlayhead(_ marker: ChewMarker) {
        guard let id = currentChewID else { return }
        state.updateMarker(chewID: id, marker: marker, to: playback.currentTime)
    }

    private func cueCurrentChew() {
        guard let chew = currentChew else { return }
        state.selectChew(id: chew.id)
        viewport.focus(on: chew, duration: max(playback.duration, 1))
        playback.setLoop(start: chew.startTS, end: chew.endTS, enabled: false)
        playback.seek(to: chew.startTS)
    }

    private func playOrPauseCurrentChewFromStart() {
        if playback.isPlaying {
            playback.pause()
            return
        }
        guard let chew = currentChew else {
            playback.play()
            return
        }
        state.selectChew(id: chew.id)
        playback.setLoop(start: chew.startTS, end: chew.endTS, enabled: false)
        playback.seek(to: chew.startTS)
        playback.play()
    }
}
