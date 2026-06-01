import SwiftUI

/// Viewport for the chew strip. `zoom = 1` shows the full duration; higher
/// values show a narrower window centered on `center`.
@MainActor
final class TimelineViewport: ObservableObject {
    @Published var center: Double = 0
    @Published var zoom: Double = 1.0

    private let maxZoom: Double = 200
    private let minZoom: Double = 1.0

    func visibleRange(duration: Double) -> ClosedRange<Double> {
        guard duration > 0 else { return 0...1 }
        let span = max(0.05, duration / max(zoom, minZoom))
        var lo = center - span / 2
        var hi = center + span / 2
        if lo < 0 { hi -= lo; lo = 0 }
        if hi > duration { lo -= (hi - duration); hi = duration }
        lo = max(0, lo)
        return lo...max(lo + 0.001, hi)
    }

    func zoomIn(pivot: Double) {
        zoom = min(maxZoom, zoom * 1.6)
        center = pivot
    }

    func zoomOut(pivot: Double) {
        zoom = max(minZoom, zoom / 1.6)
        center = pivot
    }

    func fit() {
        zoom = minZoom
    }

    /// Zoom + center on a chew with a small padding fraction.
    func focus(on chew: ReviewChew, duration: Double, paddingFraction: Double = 0.4) {
        let span = max(0.4, chew.duration * (1 + paddingFraction * 2))
        guard duration > 0 else { return }
        zoom = min(maxZoom, max(minZoom, duration / span))
        center = (chew.startTS + chew.endTS) / 2
    }

    /// Pan by a fraction of the visible window (e.g. -0.5 pans half-window left).
    func pan(byFractionOfVisible fraction: Double, duration: Double) {
        let range = visibleRange(duration: duration)
        let span = range.upperBound - range.lowerBound
        center = max(0, min(duration, center + span * fraction))
    }

    func setCenter(_ t: Double, duration: Double) {
        center = max(0, min(duration, t))
    }

    /// Recenter the viewport so the playhead sits within the inner deadband
    /// of the visible window. Callers should invoke this during playback so
    /// the playhead never scrolls off-screen.
    func follow(playhead: Double, duration: Double) {
        guard duration > 0, zoom > 1.05 else { return }
        let range = visibleRange(duration: duration)
        let span = range.upperBound - range.lowerBound
        // Deadband: keep playhead inside inner 60% of the visible window.
        let lo = range.lowerBound + span * 0.20
        let hi = range.upperBound - span * 0.20
        if playhead < lo || playhead > hi {
            center = max(0, min(duration, playhead))
        }
    }

    /// Snap the viewport so the playhead is centered (used when playback
    /// resumes after the user has panned the timeline).
    func snapToPlayhead(_ playhead: Double, duration: Double) {
        guard duration > 0, zoom > 1.05 else { return }
        center = max(0, min(duration, playhead))
    }
}
