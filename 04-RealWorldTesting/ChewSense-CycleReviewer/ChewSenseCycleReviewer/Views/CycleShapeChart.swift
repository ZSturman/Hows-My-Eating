import SwiftUI
import Charts

/// Compact graph showing a single chew cycle's mouth-open trace, with
/// start / peak / end rules and a live playhead. Mounted above the video
/// so the reviewer can see whether the auto-detected peak actually lines up
/// with the visual peak in the same glance.
struct CycleShapeChart: View {
    @EnvironmentObject var state: ReviewerState
    @EnvironmentObject var playback: PlaybackController

    /// Padding (seconds) on each side of the cycle window so the rise and
    /// fall outside the official boundaries are visible.
    private let padSeconds: Double = 0.15

    var body: some View {
        if let chew = state.selectedChew {
            content(for: chew)
                .frame(height: 110)
                .padding(.horizontal, 10)
                .padding(.vertical, 6)
                .background(Color.black.opacity(0.55), in: RoundedRectangle(cornerRadius: 8))
                .overlay(alignment: .topLeading) {
                    legend
                        .padding(8)
                }
        }
    }

    @ViewBuilder
    private func content(for chew: ReviewChew) -> some View {
        let lo = chew.startTS - padSeconds
        let hi = chew.endTS + padSeconds
        let samples = windowedSamples(in: lo...hi)
        let isReal = !samples.isEmpty
        let series: [(t: Double, v: Double)] = isReal
            ? samples
            : stylizedTriangle(for: chew)
        let yMax = max(series.map(\.v).max() ?? 1.0, 1e-6)

        Chart {
            ForEach(Array(series.enumerated()), id: \.offset) { _, sample in
                LineMark(
                    x: .value("t", sample.t),
                    y: .value("open", sample.v / yMax)
                )
                .foregroundStyle(Color.cyan.opacity(0.95))
                .interpolationMethod(.monotone)
            }
            RuleMark(x: .value("start", chew.startTS))
                .foregroundStyle(Color.green)
                .lineStyle(StrokeStyle(lineWidth: 1.5))
                .annotation(position: .top, alignment: .leading) {
                    Text("S").font(.caption2.bold()).foregroundStyle(.green)
                }
            RuleMark(x: .value("peak", chew.peakTS))
                .foregroundStyle(Color.yellow)
                .lineStyle(StrokeStyle(lineWidth: 1.5))
                .annotation(position: .top, alignment: .center) {
                    Text("P").font(.caption2.bold()).foregroundStyle(.yellow)
                }
            RuleMark(x: .value("end", chew.endTS))
                .foregroundStyle(Color.red)
                .lineStyle(StrokeStyle(lineWidth: 1.5))
                .annotation(position: .top, alignment: .trailing) {
                    Text("E").font(.caption2.bold()).foregroundStyle(.red)
                }
            RuleMark(x: .value("playhead", playback.currentTime))
                .foregroundStyle(Color.white.opacity(0.85))
                .lineStyle(StrokeStyle(lineWidth: 1, dash: [3, 2]))
        }
        .chartXScale(domain: lo...hi)
        .chartYScale(domain: 0...1.05)
        .chartXAxis {
            AxisMarks(values: .automatic(desiredCount: 4)) { value in
                AxisGridLine().foregroundStyle(Color.white.opacity(0.08))
                AxisValueLabel {
                    if let t = value.as(Double.self) {
                        Text(formatRelative(t, origin: chew.startTS))
                            .font(.caption2)
                            .foregroundStyle(.white.opacity(0.7))
                    }
                }
            }
        }
        .chartYAxis(.hidden)
    }

    private var legend: some View {
        HStack(spacing: 10) {
            Text(state.framePredictions.isEmpty ? "stylized" : "jaw-open signal")
                .font(.caption2)
                .foregroundStyle(.white.opacity(0.7))
        }
    }

    private func windowedSamples(in range: ClosedRange<Double>) -> [(t: Double, v: Double)] {
        let preds = state.framePredictions
        guard !preds.isEmpty else { return [] }
        // Linear scan; cycle windows are short (~1 s) so this is cheap.
        var out: [(Double, Double)] = []
        out.reserveCapacity(64)
        for p in preds {
            if p.ts < range.lowerBound { continue }
            if p.ts > range.upperBound { break }
            out.append((p.ts, p.mouthOpen))
        }
        return out
    }

    private func stylizedTriangle(for chew: ReviewChew) -> [(t: Double, v: Double)] {
        let lo = chew.startTS - padSeconds
        let hi = chew.endTS + padSeconds
        return [
            (lo, 0),
            (chew.startTS, 0),
            (chew.peakTS, 1),
            (chew.endTS, 0),
            (hi, 0),
        ]
    }

    private func formatRelative(_ t: Double, origin: Double) -> String {
        let d = t - origin
        return String(format: "%+.2fs", d)
    }
}
