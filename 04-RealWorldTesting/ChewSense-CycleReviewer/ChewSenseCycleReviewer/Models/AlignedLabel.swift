import Foundation

struct AlignedLabel: Identifiable {
    var id: Int { rowIndex }
    let rowIndex: Int

    let timestamp: Double
    let videoTS: Double
    var eating: Int
    var chewPhase: String
    var chewID: String
    var videoConfidence: Double
}

extension AlignedLabel {
    static let csvHeader = "timestamp,video_ts,eating,chew_phase,chew_id,video_confidence"

    func toCSVRow() -> String {
        "\(timestamp),\(videoTS),\(eating),\(chewPhase),\(chewID),\(videoConfidence)"
    }
}
