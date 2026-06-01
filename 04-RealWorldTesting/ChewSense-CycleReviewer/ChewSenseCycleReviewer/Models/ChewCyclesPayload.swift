import Foundation

/// Decoded shape of `chew_cycles.json` written by the Phase 2 bridge.
struct ChewCyclesPayload: Codable {
    let videoID: String?
    let durationS: Double?
    let timeOffset: Double?
    let nMotionRows: Int?
    let episodes: [Episode]

    struct Episode: Codable, Identifiable {
        let id: String
        let startTS: Double
        let endTS: Double
        let confidence: Double
        let chews: [Chew]

        enum CodingKeys: String, CodingKey {
            case id
            case startTS = "start_ts"
            case endTS = "end_ts"
            case confidence
            case chews
        }
    }

    struct Chew: Codable, Identifiable {
        let id: String
        let startTS: Double
        let peakTS: Double
        let endTS: Double
        let amplitude: Double?
        let confidence: Double

        enum CodingKeys: String, CodingKey {
            case id
            case startTS = "start_ts"
            case peakTS = "peak_ts"
            case endTS = "end_ts"
            case amplitude
            case confidence
        }
    }

    enum CodingKeys: String, CodingKey {
        case videoID = "video_id"
        case durationS = "duration_s"
        case timeOffset = "time_offset"
        case nMotionRows = "n_motion_rows"
        case episodes
    }
}
