import SwiftUI

/// Slimmed reviewer state: load/save sessions; create / edit / delete chews;
/// undo/redo. Span edits are preserved on JSON round-trip but not exposed.
@MainActor
final class ReviewerState: ObservableObject {
    // MARK: Workspace + sessions
    @Published var workspaceRoot: URL?
    @Published var sessions: [Session] = []
    @Published var selectedSession: Session?

    // MARK: Loaded session data
    @Published private(set) var baseRows: [AlignedLabel] = []
    @Published private(set) var alignedRows: [AlignedLabel] = []
    @Published private(set) var chewCycles: ChewCyclesPayload?
    @Published private(set) var overrides: ReviewOverrides = .empty(sessionID: "")

    // MARK: Working chews + selection
    @Published private(set) var chews: [ReviewChew] = []
    @Published private(set) var eatingSegments: [EatingSegment] = []
    @Published private(set) var framePredictions: [FramePrediction] = []
    @Published var selectedChewID: String?
    @Published var lastTouchedMarker: ChewMarker = .start

    // MARK: Playback-coupled state
    @Published var loopSelectedChew: Bool = false
    @Published var loopPadding: Double = 0.10
    @Published var useAnnotatedVideo: Bool = false

    // MARK: UI ephemera
    @Published var statusMessage: String = ""
    @Published var isDirty: Bool = false

    // MARK: Undo / redo
    private var undoStack: [Snapshot] = []
    private var redoStack: [Snapshot] = []
    var canUndo: Bool { !undoStack.isEmpty }
    var canRedo: Bool { !redoStack.isEmpty }

    private static let rootDefaultsKey = "ChewSenseCycleReviewer.workspaceRoot"
    private static let minimumMarkerGap = 0.005
    static let neighborGap = 1.0 / 30.0

    init() {
        if let path = UserDefaults.standard.string(forKey: Self.rootDefaultsKey) {
            let url = URL(fileURLWithPath: path)
            if FileManager.default.fileExists(atPath: url.path) {
                setWorkspaceRoot(url)
            }
        }
    }

    // MARK: - Workspace

    func setWorkspaceRoot(_ url: URL) {
        workspaceRoot = url
        UserDefaults.standard.set(url.path, forKey: Self.rootDefaultsKey)
        refreshSessions()
    }

    func refreshSessions() {
        guard let root = workspaceRoot else { sessions = []; return }
        sessions = SessionDiscovery(paths: WorkspacePaths(root: root)).listSessions()
    }

    // MARK: - Loading

    func loadSession(_ session: Session) {
        selectedSession = session
        do {
            baseRows = try loadAutoBaseline(for: session)
            let cyclesData = try Data(contentsOf: session.chewCyclesJSON)
            chewCycles = try JSONDecoder().decode(ChewCyclesPayload.self, from: cyclesData)
            overrides = OverridePersistence.loadIfPresent(session.overridesURL)
                ?? .empty(sessionID: session.id)
            selectedChewID = nil
            undoStack.removeAll()
            redoStack.removeAll()
            isDirty = false
            rebuildPreview()
            framePredictions = session.framePredictionsCSV
                .map { FramePredictionsLoader.load(from: $0) } ?? []
            let rawCount = chewCycles?.episodes.reduce(0) { $0 + $1.chews.count } ?? 0
            let dropped = rawCount - chews.count
            if dropped > 0 {
                statusMessage = "Loaded \(chews.count) chews (\(dropped) overlapping auto chew\(dropped == 1 ? "" : "s") removed)"
            } else {
                statusMessage = "Loaded \(chews.count) chews"
            }
        } catch {
            baseRows = []
            alignedRows = []
            chewCycles = nil
            chews = []
            eatingSegments = []
            framePredictions = []
            selectedChewID = nil
            statusMessage = "Load failed: \(error.localizedDescription)"
        }
    }

    private func loadAutoBaseline(for session: Session) throws -> [AlignedLabel] {
        let snapshot = session.derivedDir.appending(path: "motion_aligned_labels.auto.csv")
        if FileManager.default.fileExists(atPath: snapshot.path) {
            return try CSVLoader.loadAlignedLabels(from: snapshot)
        }
        return try CSVLoader.loadAlignedLabels(from: session.alignedCSV)
    }

    // MARK: - Saving

    func saveOverrides() {
        guard let session = selectedSession else { return }
        var ov = overrides
        ov.reviewedAt = ISO8601DateFormatter().string(from: Date())
        let merged = OverrideApplier.apply(ov, to: baseRows)
        do {
            try OverridePersistence.save(ov, session: session, mergedRows: merged)
            overrides = ov
            alignedRows = merged
            isDirty = false
            statusMessage = ov.verified ? "Saved (verified)" : "Saved"
            refreshSessions()
        } catch {
            statusMessage = "Save failed: \(error.localizedDescription)"
        }
    }

    func toggleVerified() {
        pushUndo()
        overrides.verified.toggle()
        isDirty = true
    }

    // MARK: - Selection

    var selectedChew: ReviewChew? {
        guard let id = selectedChewID else { return nil }
        return chews.first { $0.id == id }
    }

    var selectedChewIndex: Int? {
        guard let id = selectedChewID else { return nil }
        return chews.firstIndex { $0.id == id }
    }

    func selectChew(id: String?) {
        selectedChewID = id
    }

    @discardableResult
    func selectNextChew() -> ReviewChew? {
        guard !chews.isEmpty else { return nil }
        let idx: Int
        if let cur = selectedChewIndex {
            idx = min(cur + 1, chews.count - 1)
        } else {
            idx = 0
        }
        let c = chews[idx]
        selectedChewID = c.id
        return c
    }

    @discardableResult
    func selectPreviousChew() -> ReviewChew? {
        guard !chews.isEmpty else { return nil }
        let idx: Int
        if let cur = selectedChewIndex {
            idx = max(cur - 1, 0)
        } else {
            idx = chews.count - 1
        }
        let c = chews[idx]
        selectedChewID = c.id
        return c
    }

    @discardableResult
    func selectNearestChew(to videoTime: Double) -> ReviewChew? {
        guard let c = chews.min(by: { $0.distance(to: videoTime) < $1.distance(to: videoTime) }) else {
            return nil
        }
        selectedChewID = c.id
        return c
    }

    // MARK: - Edits

    /// Add a manual chew. Peak defaults to the midpoint between start/end.
    func addChew(start: Double, end: Double, peak: Double? = nil) {
        guard end > start else { return }
        let p = peak ?? ((start + end) / 2.0)
        guard p > start, p < end else { return }

        let overlapping = chews.filter { $0.endTS > start && $0.startTS < end }
        for existing in overlapping where existing.startTS >= start && existing.endTS <= end {
            statusMessage = "Skipped — would swallow \(existing.id)"
            return
        }
        pushUndo()
        let edit = ReviewOverrides.ChewEdit(
            id: nextManualChewID(),
            startTS: max(0, start),
            peakTS: p,
            endTS: end,
            confidence: 1.0
        )
        for existing in overlapping {
            trimNeighbor(existing, keepClearOf: start...end)
        }
        overrides.addedChews.append(edit)
        rebuildPreview()
        selectedChewID = edit.id
        isDirty = true
        statusMessage = "Added \(edit.id)"
    }

    /// Move a single marker on a chew (drag/keyboard fine-tune).
    /// `recordUndo` should be false during drag-in-progress; call once
    /// at drag start with `recordUndo: true` instead.
    @discardableResult
    func updateMarker(chewID: String, marker: ChewMarker, to time: Double, recordUndo: Bool = true) -> ReviewChew? {
        guard let chew = chews.first(where: { $0.id == chewID }) else { return nil }
        if recordUndo { pushUndo() }
        let clamped = clampMarker(chew: chew, marker: marker, proposed: time)
        let updated = chewWithUpdatedMarker(chew, marker: marker, time: clamped)
        applyChewEdit(updated)
        // Editing a chew invalidates a prior verification.
        overrides.verifiedChewIDs.removeAll { $0 == chewID }
        rebuildPreview()
        selectedChewID = updated.id
        lastTouchedMarker = marker
        isDirty = true
        return chews.first { $0.id == updated.id }
    }

    func nudgeLastTouchedMarker(by delta: Double) {
        guard let c = selectedChew else { return }
        let target = c.timestamp(for: lastTouchedMarker) + delta
        updateMarker(chewID: c.id, marker: lastTouchedMarker, to: target)
    }

    /// Delete the selected chew, or fallback to the chew under `videoTime`.
    func deleteSelectedOrAt(videoTime: Double) {
        let target = selectedChew ?? chews.first { $0.contains(videoTime) }
        guard let chew = target else { return }
        pushUndo()
        switch chew.source {
        case .added:
            overrides.addedChews.removeAll { $0.id == chew.id }
        case .auto, .edited:
            overrides.editedChews.removeAll { $0.id == chew.id }
            if !overrides.deletedChewIDs.contains(chew.id) {
                overrides.deletedChewIDs.append(chew.id)
            }
        }
        overrides.verifiedChewIDs.removeAll { $0 == chew.id }
        rebuildPreview()
        if selectedChewID == chew.id { selectedChewID = nil }
        isDirty = true
        statusMessage = "Deleted \(chew.id)"
    }

    /// Drop user edits on `chewID`, restoring the auto baseline.
    func revertChewToAuto(id: String) {
        guard chewCycles?.episodes.contains(where: { $0.chews.contains { $0.id == id } }) ?? false else {
            statusMessage = "No auto baseline for \(id)"
            return
        }
        pushUndo()
        overrides.editedChews.removeAll { $0.id == id }
        overrides.deletedChewIDs.removeAll { $0 == id }
        rebuildPreview()
        selectedChewID = id
        isDirty = true
        statusMessage = "Reverted \(id) to auto"
    }

    // MARK: - Undo / redo

    private struct Snapshot {
        var overrides: ReviewOverrides
        var selectedChewID: String?
    }

    private func pushUndo() {
        undoStack.append(Snapshot(overrides: overrides, selectedChewID: selectedChewID))
        if undoStack.count > 100 { undoStack.removeFirst(undoStack.count - 100) }
        redoStack.removeAll()
    }

    func undo() {
        guard let snap = undoStack.popLast() else { return }
        redoStack.append(Snapshot(overrides: overrides, selectedChewID: selectedChewID))
        overrides = snap.overrides
        selectedChewID = snap.selectedChewID
        rebuildPreview()
        isDirty = true
        statusMessage = "Undo"
    }

    func redo() {
        guard let snap = redoStack.popLast() else { return }
        undoStack.append(Snapshot(overrides: overrides, selectedChewID: selectedChewID))
        overrides = snap.overrides
        selectedChewID = snap.selectedChewID
        rebuildPreview()
        isDirty = true
        statusMessage = "Redo"
    }

    // MARK: - Internals

    private func clampMarker(chew: ReviewChew, marker: ChewMarker, proposed: Double) -> Double {
        let gap = Self.minimumMarkerGap
        let neighborGap = Self.neighborGap
        var t = max(0, proposed)
        let others = chews.filter { $0.id != chew.id }.sorted { $0.startTS < $1.startTS }
        let prev = others.last { $0.startTS < chew.startTS }
        let next = others.first { $0.startTS > chew.startTS }
        switch marker {
        case .start:
            if let prev { t = max(t, prev.endTS + neighborGap) }
            t = min(t, chew.peakTS - gap)
        case .peak:
            t = max(t, chew.startTS + gap)
            t = min(t, chew.endTS - gap)
        case .end:
            if let next { t = min(t, next.startTS - neighborGap) }
            t = max(t, chew.peakTS + gap)
        }
        return t
    }

    private func chewWithUpdatedMarker(_ chew: ReviewChew, marker: ChewMarker, time: Double) -> ReviewChew {
        var u = chew
        switch marker {
        case .start: u.startTS = time
        case .peak:  u.peakTS  = time
        case .end:   u.endTS   = time
        }
        return u
    }

    private func applyChewEdit(_ chew: ReviewChew) {
        let edit = chew.asChewEdit(confidence: chew.confidence)
        switch chew.source {
        case .added:
            if let idx = overrides.addedChews.firstIndex(where: { $0.id == chew.id }) {
                overrides.addedChews[idx] = edit
            } else {
                overrides.addedChews.append(edit)
            }
        case .auto, .edited:
            overrides.editedChews.removeAll { $0.id == chew.id }
            overrides.editedChews.append(edit)
        }
    }

    private func trimNeighbor(_ neighbor: ReviewChew, keepClearOf range: ClosedRange<Double>) {
        let gap = Self.neighborGap
        let inner = Self.minimumMarkerGap
        var trimmed = neighbor
        if neighbor.endTS > range.lowerBound && neighbor.startTS < range.lowerBound {
            trimmed.endTS = max(neighbor.startTS + 2 * inner, range.lowerBound - gap)
            if trimmed.peakTS >= trimmed.endTS {
                trimmed.peakTS = max(trimmed.startTS + inner, trimmed.endTS - inner)
            }
        } else if neighbor.startTS < range.upperBound && neighbor.endTS > range.upperBound {
            trimmed.startTS = min(neighbor.endTS - 2 * inner, range.upperBound + gap)
            if trimmed.peakTS <= trimmed.startTS {
                trimmed.peakTS = min(trimmed.endTS - inner, trimmed.startTS + inner)
            }
        } else { return }
        guard trimmed.startTS + 2 * inner < trimmed.endTS else { return }
        applyChewEdit(trimmed)
    }

    private func rebuildPreview() {
        alignedRows = OverrideApplier.apply(overrides, to: baseRows)
        chews = buildChews()
        eatingSegments = Self.buildEatingSegments(from: alignedRows)
        if let sel = selectedChewID, !chews.contains(where: { $0.id == sel }) {
            selectedChewID = nil
        }
    }

    private func buildChews() -> [ReviewChew] {
        var byID: [String: ReviewChew] = [:]
        if let chewCycles {
            for episode in chewCycles.episodes {
                for c in episode.chews {
                    byID[c.id] = ReviewChew(
                        id: c.id, startTS: c.startTS, peakTS: c.peakTS, endTS: c.endTS,
                        confidence: c.confidence, source: .auto
                    )
                }
            }
        }
        for id in overrides.deletedChewIDs { byID.removeValue(forKey: id) }
        for e in overrides.editedChews {
            byID[e.id] = ReviewChew(
                id: e.id, startTS: e.startTS, peakTS: e.peakTS, endTS: e.endTS,
                confidence: e.confidence, source: .edited
            )
        }
        for a in overrides.addedChews {
            byID[a.id] = ReviewChew(
                id: a.id, startTS: a.startTS, peakTS: a.peakTS, endTS: a.endTS,
                confidence: a.confidence, source: .added
            )
        }
        let sorted = byID.values.sorted { lhs, rhs in
            if lhs.startTS == rhs.startTS { return lhs.id < rhs.id }
            return lhs.startTS < rhs.startTS
        }
        return Self.removeOverlaps(from: sorted)
    }

    /// Drop or trim chews from `sorted` (already in start-time order) so that
    /// every chew satisfies  `start >= prev.end + neighborGap`.
    /// Auto chews that overlap are dropped (they come from the data and will be
    /// fixed at the source); user-added/edited chews are never silently dropped —
    /// only trimmed at their start if they encroach on a prior chew.
    private static func removeOverlaps(from sorted: [ReviewChew]) -> [ReviewChew] {
        let gap = Self.neighborGap
        var result: [ReviewChew] = []
        var prevEnd: Double = -.infinity
        for chew in sorted {
            guard chew.startTS < chew.endTS, chew.peakTS > chew.startTS, chew.peakTS <= chew.endTS else {
                continue  // malformed — skip
            }
            if chew.startTS >= prevEnd + gap {
                result.append(chew)
                prevEnd = chew.endTS
            } else if chew.source != .auto {
                // User edit: trim start forward to clear the previous chew.
                let newStart = prevEnd + gap
                if newStart < chew.peakTS {
                    var trimmed = chew
                    trimmed.startTS = newStart
                    result.append(trimmed)
                    prevEnd = trimmed.endTS
                }
                // If even the trimmed version would be malformed, drop it.
            }
            // Auto chew that overlaps: silently drop — flag in status on load.
        }
        return result
    }

    private func nextManualChewID() -> String {
        let existing = Set(chews.map(\.id))
            .union(overrides.addedChews.map(\.id))
            .union(overrides.editedChews.map(\.id))
        var index = overrides.addedChews.count
        while true {
            let candidate = String(format: "manual_%04d", index)
            if !existing.contains(candidate) { return candidate }
            index += 1
        }
    }

    // MARK: - Stats

    var stats: (visible: Int, added: Int, edited: Int, deleted: Int) {
        (chews.count,
         overrides.addedChews.count,
         overrides.editedChews.count,
         overrides.deletedChewIDs.count)
    }

    var verifiedCount: Int { overrides.verifiedChewIDs.count }

    func isVerified(id: String) -> Bool {
        overrides.verifiedChewIDs.contains(id)
    }

    // MARK: - Verify workflow

    func toggleChewVerified(id: String) {
        pushUndo()
        if let idx = overrides.verifiedChewIDs.firstIndex(of: id) {
            overrides.verifiedChewIDs.remove(at: idx)
            statusMessage = "Unverified \(id)"
        } else {
            overrides.verifiedChewIDs.append(id)
            statusMessage = "Verified \(id)"
        }
        isDirty = true
    }

    /// Mark the selected chew verified (idempotent) and advance to the next
    /// unverified chew. Returns the new selection so callers can seek/play.
    @discardableResult
    func verifyAndAdvance() -> ReviewChew? {
        guard let cur = selectedChew else { return nil }
        if !overrides.verifiedChewIDs.contains(cur.id) {
            pushUndo()
            overrides.verifiedChewIDs.append(cur.id)
            isDirty = true
        }
        return advanceToNextUnverified() ?? selectNextChew()
    }

    @discardableResult
    func advanceToNextUnverified() -> ReviewChew? {
        let startIdx = (selectedChewIndex ?? -1) + 1
        if startIdx < chews.count {
            for i in startIdx..<chews.count where !isVerified(id: chews[i].id) {
                selectedChewID = chews[i].id
                return chews[i]
            }
        }
        // Wrap from start.
        for i in 0..<chews.count where !isVerified(id: chews[i].id) {
            selectedChewID = chews[i].id
            return chews[i]
        }
        statusMessage = "All chews verified"
        return nil
    }

    // MARK: - Marker hop

    /// Flat sorted list of every (time, chewID, marker) tuple.
    var allMarkers: [(time: Double, chewID: String, marker: ChewMarker)] {
        var out: [(Double, String, ChewMarker)] = []
        for c in chews {
            out.append((c.startTS, c.id, .start))
            out.append((c.peakTS, c.id, .peak))
            out.append((c.endTS, c.id, .end))
        }
        return out.sorted { $0.0 < $1.0 }
    }

    func nextMarker(after time: Double) -> (time: Double, chewID: String, marker: ChewMarker)? {
        allMarkers.first { $0.time > time + 0.001 }
    }

    func previousMarker(before time: Double) -> (time: Double, chewID: String, marker: ChewMarker)? {
        allMarkers.last { $0.time < time - 0.001 }
    }

    // MARK: - Eating segments

    /// Contiguous run of `eating == 1` rows in `alignedRows`. Identified by
    /// integer row bounds so we can locate the segment in `alignedRows` even
    /// after edits shift the time range slightly.
    struct EatingSegment: Identifiable, Equatable {
        let id: String          // "<startRow>-<endRow>"
        let startRow: Int       // inclusive index into alignedRows
        let endRow: Int         // inclusive
        let startTS: Double
        let endTS: Double
        var duration: Double { max(0, endTS - startTS) }
    }

    private static func buildEatingSegments(from rows: [AlignedLabel]) -> [EatingSegment] {
        guard !rows.isEmpty else { return [] }
        var out: [EatingSegment] = []
        var i = 0
        while i < rows.count {
            guard rows[i].eating == 1 else { i += 1; continue }
            let start = i
            while i < rows.count && rows[i].eating == 1 { i += 1 }
            let end = i - 1
            // Pad to row boundaries (half-frame on each side) for visual extent.
            let halfFrame = 1.0 / 60.0
            let s = max(0, rows[start].videoTS - halfFrame)
            let e = rows[end].videoTS + halfFrame
            out.append(EatingSegment(
                id: "\(start)-\(end)",
                startRow: start,
                endRow: end,
                startTS: s,
                endTS: e
            ))
        }
        return out
    }

    /// Move one edge of an eating segment to a new video time. Persists the
    /// change as a `flippedEatingSpans` entry covering the rows between the
    /// old and new boundary, so saving + reloading reproduces the same edge.
    func editEatingEdge(segmentID: String, edge: EatingEdge, to time: Double, recordUndo: Bool = true) {
        guard let seg = eatingSegments.first(where: { $0.id == segmentID }) else { return }
        guard !alignedRows.isEmpty else { return }
        let snapped = (time * 30.0).rounded() / 30.0
        switch edge {
        case .start:
            // We want every row whose videoTS is between min(old, new) and
            // max(old, new) to flip its eating value. The boundary row inside
            // the segment must remain eating; the row just outside must not.
            let oldEdge = seg.startTS
            let lo = min(snapped, oldEdge)
            let hi = max(snapped, oldEdge)
            // Build a span over the rows strictly inside (lo, hi).
            guard hi - lo > 1e-4 else { return }
            if recordUndo { pushUndo() }
            overrides.flippedEatingSpans.append(.init(startTS: lo, endTS: hi))
            isDirty = true
            rebuildPreview()
        case .end:
            let oldEdge = seg.endTS
            let lo = min(snapped, oldEdge)
            let hi = max(snapped, oldEdge)
            guard hi - lo > 1e-4 else { return }
            if recordUndo { pushUndo() }
            overrides.flippedEatingSpans.append(.init(startTS: lo, endTS: hi))
            isDirty = true
            rebuildPreview()
        }
    }

    enum EatingEdge { case start, end }

    /// The eating segment that contains or surrounds the given chew, if any.
    func eatingSegment(enclosing chew: ReviewChew) -> EatingSegment? {
        eatingSegments.first { $0.startTS <= chew.peakTS && $0.endTS >= chew.peakTS }
    }
}
