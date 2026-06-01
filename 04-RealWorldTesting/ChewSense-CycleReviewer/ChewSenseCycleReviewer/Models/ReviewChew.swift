import Foundation

enum ChewMarker: String, CaseIterable, Identifiable, Hashable {
    case start
    case peak
    case end

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .start: "Start"
        case .peak: "Peak"
        case .end: "End"
        }
    }
}

struct ReviewChew: Identifiable, Hashable {
    enum Source: String, Hashable {
        case auto
        case added
        case edited
    }

    var id: String
    var startTS: Double
    var peakTS: Double
    var endTS: Double
    var confidence: Double
    var source: Source

    var duration: Double { max(0, endTS - startTS) }

    func contains(_ videoTime: Double) -> Bool {
        videoTime >= startTS && videoTime <= endTS
    }

    func distance(to videoTime: Double) -> Double {
        if contains(videoTime) { return 0 }
        return min(abs(videoTime - startTS), abs(videoTime - endTS))
    }

    func asChewEdit(confidence overrideConfidence: Double? = nil) -> ReviewOverrides.ChewEdit {
        ReviewOverrides.ChewEdit(
            id: id,
            startTS: startTS,
            peakTS: peakTS,
            endTS: endTS,
            confidence: overrideConfidence ?? confidence
        )
    }

    func timestamp(for marker: ChewMarker) -> Double {
        switch marker {
        case .start: startTS
        case .peak: peakTS
        case .end: endTS
        }
    }
}
