import SwiftUI
import AppKit

/// Bottom deck: chew strip + transport bar + zoom controls.
struct BottomDeck: View {
    var body: some View {
        VStack(spacing: 8) {
            ChewStripView()
                .frame(height: 80)
            TransportBar()
                .frame(height: 36)
        }
        .padding(10)
        .background(.black.opacity(0.55), in: RoundedRectangle(cornerRadius: 12, style: .continuous))
    }
}

// MARK: - Chew strip

/// Horizontal time strip showing every chew. Single drag handles either
/// fine-tuning a marker (drag begins on a handle) or creating a new chew
/// (drag begins in empty space). Scroll = pan; pinch / scroll-with-modifier = zoom.
struct ChewStripView: View {
    @EnvironmentObject var state: ReviewerState
    @EnvironmentObject var playback: PlaybackController
    @EnvironmentObject var viewport: TimelineViewport

    @State private var activeDrag: ActiveDrag?
    private let handleHitRadius: CGFloat = 10
    private let eatingHandleHitRadius: CGFloat = 8

    private enum ActiveDrag {
        case create(startT: Double, currentT: Double)
        case marker(chewID: String, marker: ChewMarker)
        case eatingEdge(segmentID: String, edge: ReviewerState.EatingEdge)
        case scrub
    }

    var body: some View {
        GeometryReader { geo in
            let duration = max(playback.duration, 1)
            let range = viewport.visibleRange(duration: duration)
            let span = max(0.001, range.upperBound - range.lowerBound)
            let width = geo.size.width

            ZStack(alignment: .topLeading) {
                Rectangle()
                    .fill(Color.white.opacity(0.06))
                    .clipShape(RoundedRectangle(cornerRadius: 6))

                ticks(range: range, span: span, width: width)

                // Eating segments (drawn behind chew blocks)
                ForEach(state.eatingSegments) { seg in
                    eatingBand(seg, range: range, span: span, width: width)
                        .allowsHitTesting(false)
                }

                ForEach(state.chews) { chew in
                    chewBlock(chew, range: range, span: span, width: width)
                        .allowsHitTesting(false)
                }

                if case let .create(s, c) = activeDrag {
                    let lo = min(s, c), hi = max(s, c)
                    Rectangle()
                        .fill(Color.cyan.opacity(0.45))
                        .overlay(RoundedRectangle(cornerRadius: 4).stroke(Color.cyan, lineWidth: 1))
                        .frame(width: max(2, xFor(hi, range: range, span: span, width: width) - xFor(lo, range: range, span: span, width: width)),
                               height: 56)
                        .offset(x: xFor(lo, range: range, span: span, width: width), y: 14)
                        .allowsHitTesting(false)
                }

                Rectangle()
                    .fill(Color.yellow)
                    .frame(width: 2, height: 80)
                    .offset(x: xFor(playback.currentTime, range: range, span: span, width: width) - 1, y: 0)
                    .allowsHitTesting(false)
            }
            .clipped()
            .contentShape(Rectangle())
            .gesture(stripDrag(width: width, range: range, span: span, duration: duration))
            .onTapGesture { loc in handleTap(at: loc, width: width, range: range, span: span) }
            .onContinuousHover { _ in } // ensure scroll events route here
            .modifier(ScrollPanZoom(width: width, range: range, span: span, duration: duration))
            .onChange(of: playback.currentTime) { _, t in
                if playback.isPlaying {
                    viewport.follow(playhead: t, duration: duration)
                }
            }
        }
    }

    // MARK: - Coordinate helpers

    private func xFor(_ t: Double, range: ClosedRange<Double>, span: Double, width: CGFloat) -> CGFloat {
        let frac = (t - range.lowerBound) / span
        return CGFloat(frac) * width
    }

    private func tFor(_ x: CGFloat, range: ClosedRange<Double>, span: Double, width: CGFloat) -> Double {
        let frac = max(0, min(1, Double(x / max(width, 1))))
        return range.lowerBound + frac * span
    }

    // MARK: - Ticks

    @ViewBuilder
    private func ticks(range: ClosedRange<Double>, span: Double, width: CGFloat) -> some View {
        let step: Double = pickTickStep(span: span)
        let firstTick = (range.lowerBound / step).rounded(.up) * step
        let count = max(0, Int(((range.upperBound - firstTick) / step).rounded(.down)))
        ForEach(0...count, id: \.self) { i in
            let t = firstTick + Double(i) * step
            let x = xFor(t, range: range, span: span, width: width)
            ZStack(alignment: .topLeading) {
                Rectangle().fill(Color.white.opacity(0.10)).frame(width: 1, height: 80).offset(x: x)
                Text(String(format: "%.2fs", t))
                    .font(.system(size: 9, design: .monospaced))
                    .foregroundStyle(.white.opacity(0.55))
                    .offset(x: x + 2, y: 64)
            }
        }
    }

    private func pickTickStep(span: Double) -> Double {
        let candidates: [Double] = [0.1, 0.25, 0.5, 1, 2, 5, 10, 30, 60, 120, 300]
        for c in candidates where span / c <= 12 { return c }
        return 600
    }

    // MARK: - Block rendering

    @ViewBuilder
    private func eatingBand(_ seg: ReviewerState.EatingSegment, range: ClosedRange<Double>, span: Double, width: CGFloat) -> some View {
        if seg.endTS < range.lowerBound || seg.startTS > range.upperBound {
            EmptyView()
        } else {
            let x0 = xFor(seg.startTS, range: range, span: span, width: width)
            let x1 = xFor(seg.endTS, range: range, span: span, width: width)
            let w = max(2, x1 - x0)
            ZStack(alignment: .topLeading) {
                RoundedRectangle(cornerRadius: 3)
                    .fill(Color.blue.opacity(0.18))
                    .overlay(
                        RoundedRectangle(cornerRadius: 3)
                            .stroke(Color.blue.opacity(0.55), lineWidth: 1)
                    )
                    .frame(width: w, height: 70)
                    .offset(x: x0, y: 5)
                // Edge grabbers (visual only — drag is handled in stripDrag)
                Capsule()
                    .fill(Color.blue.opacity(0.85))
                    .frame(width: 3, height: 70)
                    .offset(x: x0 - 1, y: 5)
                Capsule()
                    .fill(Color.blue.opacity(0.85))
                    .frame(width: 3, height: 70)
                    .offset(x: x1 - 1, y: 5)
                Text("eating · \(String(format: "%.1fs", seg.duration))")
                    .font(.system(size: 9, design: .monospaced))
                    .foregroundStyle(.white.opacity(0.7))
                    .padding(.horizontal, 3)
                    .background(Color.blue.opacity(0.35), in: RoundedRectangle(cornerRadius: 2))
                    .offset(x: x0 + 4, y: 6)
            }
        }
    }

    @ViewBuilder
    private func chewBlock(_ chew: ReviewChew, range: ClosedRange<Double>, span: Double, width: CGFloat) -> some View {
        // Skip rendering if entirely outside the visible range.
        if chew.endTS < range.lowerBound || chew.startTS > range.upperBound {
            EmptyView()
        } else {
            let x0 = xFor(chew.startTS, range: range, span: span, width: width)
            let x1 = xFor(chew.endTS, range: range, span: span, width: width)
            let xp = xFor(chew.peakTS, range: range, span: span, width: width)
            let isSelected = state.selectedChewID == chew.id
            let isVerified = state.isVerified(id: chew.id)
            let color = sourceColor(chew.source)

            ZStack(alignment: .topLeading) {
                RoundedRectangle(cornerRadius: 4)
                    .fill(color.opacity(isSelected ? 0.50 : 0.25))
                    .overlay(
                        RoundedRectangle(cornerRadius: 4)
                            .stroke(isSelected ? Color.white : color, lineWidth: isSelected ? 2 : 1)
                    )
                    .frame(width: max(3, x1 - x0), height: 36)
                    .offset(x: x0, y: 22)

                // Distinct markers
                StartMarker().frame(width: 14, height: 16).offset(x: x0 - 7, y: 14)
                PeakMarker().frame(width: 14, height: 14).offset(x: xp - 7, y: 36)
                EndMarker().frame(width: 14, height: 16).offset(x: x1 - 7, y: 14)

                // Verified check
                if isVerified {
                    Image(systemName: "checkmark.seal.fill")
                        .font(.system(size: 12, weight: .bold))
                        .foregroundStyle(Color.green)
                        .background(Circle().fill(Color.black.opacity(0.7)).frame(width: 16, height: 16))
                        .offset(x: (x0 + x1) / 2 - 8, y: 0)
                }

                // Label
                if (x1 - x0) > 36 {
                    Text(chew.id.replacingOccurrences(of: "manual_", with: "M"))
                        .font(.system(.caption2, design: .monospaced))
                        .foregroundStyle(.white)
                        .padding(.horizontal, 3)
                        .background(Color.black.opacity(0.45), in: RoundedRectangle(cornerRadius: 2))
                        .offset(x: x0 + 4, y: 26)
                }
            }
        }
    }

    // MARK: - Hit testing

    private func hitMarker(at x: CGFloat, range: ClosedRange<Double>, span: Double, width: CGFloat) -> (chewID: String, marker: ChewMarker)? {
        for chew in state.chews {
            let x0 = xFor(chew.startTS, range: range, span: span, width: width)
            let x1 = xFor(chew.endTS, range: range, span: span, width: width)
            let xp = xFor(chew.peakTS, range: range, span: span, width: width)
            if abs(x - x0) <= handleHitRadius { return (chew.id, .start) }
            if abs(x - x1) <= handleHitRadius { return (chew.id, .end) }
            if abs(x - xp) <= handleHitRadius { return (chew.id, .peak) }
        }
        return nil
    }

    /// Hit eating-segment edges. Only the outer rim is targeted, so drags
    /// inside an eating band don't accidentally grab an edge.
    private func hitEatingEdge(at x: CGFloat, range: ClosedRange<Double>, span: Double, width: CGFloat) -> (segmentID: String, edge: ReviewerState.EatingEdge)? {
        for seg in state.eatingSegments {
            let x0 = xFor(seg.startTS, range: range, span: span, width: width)
            let x1 = xFor(seg.endTS, range: range, span: span, width: width)
            if abs(x - x0) <= eatingHandleHitRadius { return (seg.id, .start) }
            if abs(x - x1) <= eatingHandleHitRadius { return (seg.id, .end) }
        }
        return nil
    }

    private func chew(at t: Double) -> ReviewChew? {
        state.chews.first { $0.contains(t) }
    }

    // MARK: - Tap

    private func handleTap(at loc: CGPoint, width: CGFloat, range: ClosedRange<Double>, span: Double) {
        let t = tFor(loc.x, range: range, span: span, width: width)
        if let chew = chew(at: t) {
            // Cycle-selected state: select chew and seek to its start so the
            // user can hit Space to play just this cycle. Never auto-play.
            state.selectChew(id: chew.id)
            playback.seek(to: chew.startTS)
        } else {
            state.selectChew(id: nil)
            playback.seek(to: t)
        }
    }

    // MARK: - Unified drag

    private func stripDrag(width: CGFloat, range: ClosedRange<Double>, span: Double, duration: Double) -> some Gesture {
        DragGesture(minimumDistance: 2)
            .onChanged { g in
                let xStart = g.startLocation.x
                let xNow = max(0, min(g.location.x, width))
                let tNow = tFor(xNow, range: range, span: span, width: width)
                if activeDrag == nil {
                    if let hit = hitMarker(at: xStart, range: range, span: span, width: width) {
                        playback.suppressLoop = true
                        state.selectChew(id: hit.chewID)
                        state.lastTouchedMarker = hit.marker
                        state.updateMarker(chewID: hit.chewID, marker: hit.marker, to: tNow, recordUndo: true)
                        activeDrag = .marker(chewID: hit.chewID, marker: hit.marker)
                    } else if let hit = hitEatingEdge(at: xStart, range: range, span: span, width: width) {
                        playback.suppressLoop = true
                        state.editEatingEdge(segmentID: hit.segmentID, edge: hit.edge, to: tNow, recordUndo: true)
                        activeDrag = .eatingEdge(segmentID: hit.segmentID, edge: hit.edge)
                    } else {
                        let tStart = tFor(xStart, range: range, span: span, width: width)
                        if chew(at: tStart) != nil {
                            // Drag inside an existing chew → scrub
                            playback.seek(to: tNow)
                            activeDrag = .scrub
                        } else {
                            activeDrag = .create(startT: tStart, currentT: tNow)
                        }
                    }
                } else {
                    switch activeDrag! {
                    case .marker(let id, let m):
                        state.updateMarker(chewID: id, marker: m, to: tNow, recordUndo: false)
                        playback.seek(to: tNow)
                    case .eatingEdge(let segID, let edge):
                        state.editEatingEdge(segmentID: segID, edge: edge, to: tNow, recordUndo: false)
                    case .create(let s, _):
                        activeDrag = .create(startT: s, currentT: tNow)
                    case .scrub:
                        playback.seek(to: tNow)
                    }
                }
            }
            .onEnded { g in
                let xNow = max(0, min(g.location.x, width))
                let tNow = tFor(xNow, range: range, span: span, width: width)
                switch activeDrag {
                case .marker, .eatingEdge:
                    playback.suppressLoop = false
                case .create(let s, _):
                    let lo = min(s, tNow), hi = max(s, tNow)
                    if hi - lo >= 0.08, chew(at: (lo + hi) / 2) == nil {
                        state.addChew(start: lo, end: hi)
                    }
                case .scrub, .none: break
                }
                activeDrag = nil
            }
    }

    private func sourceColor(_ source: ReviewChew.Source) -> Color {
        switch source {
        case .auto: .gray
        case .added: .blue
        case .edited: .orange
        }
    }
}

// MARK: - Marker shapes

/// Green right-pointing chevron — Start.
struct StartMarker: View {
    var body: some View {
        Triangle(direction: .right)
            .fill(Color.green)
            .overlay(Triangle(direction: .right).stroke(Color.white, lineWidth: 1))
            .help("Start (green)")
    }
}

/// Yellow diamond — Peak.
struct PeakMarker: View {
    var body: some View {
        Diamond()
            .fill(Color.yellow)
            .overlay(Diamond().stroke(Color.black, lineWidth: 1))
            .help("Peak (yellow)")
    }
}

/// Red left-pointing chevron — End.
struct EndMarker: View {
    var body: some View {
        Triangle(direction: .left)
            .fill(Color.red)
            .overlay(Triangle(direction: .left).stroke(Color.white, lineWidth: 1))
            .help("End (red)")
    }
}

private struct Triangle: Shape {
    enum Direction { case left, right }
    let direction: Direction
    func path(in rect: CGRect) -> Path {
        var p = Path()
        switch direction {
        case .right:
            p.move(to: CGPoint(x: rect.minX, y: rect.minY))
            p.addLine(to: CGPoint(x: rect.maxX, y: rect.midY))
            p.addLine(to: CGPoint(x: rect.minX, y: rect.maxY))
        case .left:
            p.move(to: CGPoint(x: rect.maxX, y: rect.minY))
            p.addLine(to: CGPoint(x: rect.minX, y: rect.midY))
            p.addLine(to: CGPoint(x: rect.maxX, y: rect.maxY))
        }
        p.closeSubpath()
        return p
    }
}

private struct Diamond: Shape {
    func path(in rect: CGRect) -> Path {
        var p = Path()
        p.move(to: CGPoint(x: rect.midX, y: rect.minY))
        p.addLine(to: CGPoint(x: rect.maxX, y: rect.midY))
        p.addLine(to: CGPoint(x: rect.midX, y: rect.maxY))
        p.addLine(to: CGPoint(x: rect.minX, y: rect.midY))
        p.closeSubpath()
        return p
    }
}

// MARK: - Scroll & pinch handling

private struct ScrollPanZoom: ViewModifier {
    let width: CGFloat
    let range: ClosedRange<Double>
    let span: Double
    let duration: Double
    @EnvironmentObject var viewport: TimelineViewport
    @EnvironmentObject var playback: PlaybackController

    func body(content: Content) -> some View {
        content.background(
            ScrollEventCatcher { event in
                let mods = event.modifierFlags
                let dx = Double(event.scrollingDeltaX)
                let dy = Double(event.scrollingDeltaY)

                if mods.contains(.command) || mods.contains(.option) {
                    // Zoom around current playhead.
                    let pivot = playback.currentTime
                    let mag = abs(dy) > abs(dx) ? dy : dx
                    if mag > 0 { viewport.zoomIn(pivot: pivot) }
                    else if mag < 0 { viewport.zoomOut(pivot: pivot) }
                    return
                }
                // While the video is playing the playhead must remain in
                // frame, so manual scroll-pan is suppressed during playback.
                if playback.isPlaying { return }

                // Always pan horizontally if dx != 0 (trackpad or mouse).
                if dx != 0 {
                    let multiplier = mods.contains(.shift) ? 4.0 : 1.0
                    let frac = -dx * multiplier / Double(max(width, 1))
                    viewport.pan(byFractionOfVisible: frac, duration: duration)
                    return
                }
                // If only dy (vertical scroll), pan horizontally as fallback (for mouse wheel).
                if dy != 0 {
                    let multiplier = mods.contains(.shift) ? 4.0 : 1.0
                    let frac = -dy * multiplier / Double(max(width, 1))
                    viewport.pan(byFractionOfVisible: frac, duration: duration)
                }
            }
        )
    }
}

private struct ScrollEventCatcher: NSViewRepresentable {
    let onScroll: (NSEvent) -> Void

    func makeNSView(context: Context) -> ScrollNSView {
        let v = ScrollNSView()
        v.onScroll = onScroll
        return v
    }
    func updateNSView(_ nsView: ScrollNSView, context: Context) {
        nsView.onScroll = onScroll
    }

    static func dismantleNSView(_ nsView: ScrollNSView, coordinator: ()) {
        nsView.removeMonitor()
    }
}

final class ScrollNSView: NSView {
    var onScroll: ((NSEvent) -> Void)?

    private var monitor: Any?

    override func viewDidMoveToWindow() {
        super.viewDidMoveToWindow()
        if window == nil {
            removeMonitor()
        } else {
            installMonitor()
        }
    }

    private func installMonitor() {
        guard monitor == nil else { return }
        monitor = NSEvent.addLocalMonitorForEvents(matching: .scrollWheel) { [weak self] event in
            guard let self else { return event }
            guard let owningWindow = self.window,
                  let eventWindow = event.window,
                  eventWindow === owningWindow else { return event }
            let localPoint = self.convert(event.locationInWindow, from: nil)
            guard self.bounds.contains(localPoint) else { return event }
            self.onScroll?(event)
            return nil
        }
    }

    func removeMonitor() {
        if let monitor {
            NSEvent.removeMonitor(monitor)
            self.monitor = nil
        }
    }

    override func scrollWheel(with event: NSEvent) {
        onScroll?(event)
    }
    override var acceptsFirstResponder: Bool { true }

    deinit {
        removeMonitor()
    }
}

// MARK: - Transport bar

struct TransportBar: View {
    @EnvironmentObject var state: ReviewerState
    @EnvironmentObject var playback: PlaybackController
    @EnvironmentObject var viewport: TimelineViewport

    var body: some View {
        HStack(spacing: 10) {
            Button { if let c = state.selectPreviousChew() { playback.seek(to: c.startTS) } } label: {
                Image(systemName: "backward.end.fill")
            }
            .buttonStyle(.plain).help("Previous chew (P)")

            Button { playback.skip(by: -1) } label: {
                Image(systemName: "gobackward.1")
            }
            .buttonStyle(.plain).help("−1 s (J)")

            Button { playOrPauseFromSelectedCycleStart() } label: {
                Image(systemName: playback.isPlaying ? "pause.fill" : "play.fill")
                    .frame(width: 26, height: 26)
            }
            .buttonStyle(.plain).help("Play / pause (Space)")

            Button { playback.skip(by: 1) } label: {
                Image(systemName: "goforward.1")
            }
            .buttonStyle(.plain).help("+1 s (L)")

            Button { if let c = state.selectNextChew() { playback.seek(to: c.startTS) } } label: {
                Image(systemName: "forward.end.fill")
            }
            .buttonStyle(.plain).help("Next chew (N)")

            Slider(value: scrubberBinding, in: 0...max(playback.duration, 0.001))
                .controlSize(.small)
                .tint(.yellow)

            Text(String(format: "%@ / %@", formatTime(playback.currentTime), formatTime(playback.duration)))
                .font(.system(.caption, design: .monospaced).monospacedDigit())
                .foregroundStyle(.white)

            Picker("Rate", selection: rateBinding) {
                ForEach([0.25, 0.5, 0.75, 1.0, 1.5, 2.0], id: \.self) { r in
                    Text(String(format: "%.2gx", r)).tag(r)
                }
            }
            .labelsHidden()
            .frame(width: 84)

            Toggle(isOn: $state.loopSelectedChew) {
                Image(systemName: "repeat")
            }
            .toggleStyle(.button)
            .help("Loop selected chew (R)")
            .disabled(state.selectedChew == nil)

            Divider().frame(height: 18)

            Button { viewport.zoomOut(pivot: playback.currentTime) } label: { Image(systemName: "minus.magnifyingglass") }
                .buttonStyle(.plain).help("Zoom out (−)")
            Button { viewport.fit() } label: { Image(systemName: "arrow.up.left.and.arrow.down.right") }
                .buttonStyle(.plain).help("Fit (0)")
            Button { viewport.zoomIn(pivot: playback.currentTime) } label: { Image(systemName: "plus.magnifyingglass") }
                .buttonStyle(.plain).help("Zoom in (=)")
            Text(String(format: "%.1fx", viewport.zoom))
                .font(.system(.caption2, design: .monospaced))
                .foregroundStyle(.white.opacity(0.7))
                .frame(width: 36)
        }
        .foregroundStyle(.white)
    }

    private var scrubberBinding: Binding<Double> {
        Binding(get: { playback.currentTime }, set: {
            playback.seek(to: $0)
        })
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

    private var rateBinding: Binding<Double> {
        Binding(get: { playback.playbackRate }, set: { playback.setPlaybackRate($0) })
    }

    private func formatTime(_ s: Double) -> String {
        guard s.isFinite, s >= 0 else { return "0:00.000" }
        let mins = Int(s) / 60
        let secs = s.truncatingRemainder(dividingBy: 60)
        return String(format: "%d:%06.3f", mins, secs)
    }
}
