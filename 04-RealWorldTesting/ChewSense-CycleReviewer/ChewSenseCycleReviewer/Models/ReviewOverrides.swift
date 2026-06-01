import Foundation

/// On-disk schema for `review_overrides.json`.
///
/// `flippedEatingSpans` and `unreliableSpans` are preserved on round-trip for
/// back-compatibility with the Python pipeline, but the reviewer UI no longer
/// edits them.
struct ReviewOverrides: Codable {
    var schemaVersion: String = "1.0.0"
    var sessionID: String
    var verified: Bool
    var reviewer: String?
    var reviewedAt: String          // ISO-8601
    var addedChews: [ChewEdit]
    var deletedChewIDs: [String]
    var editedChews: [ChewEdit]
    var flippedEatingSpans: [TimeSpan]
    var unreliableSpans: [TimeSpan]
    var verifiedChewIDs: [String]
    var notes: String?

    struct ChewEdit: Codable, Identifiable, Equatable {
        var id: String
        var startTS: Double
        var peakTS: Double
        var endTS: Double
        var confidence: Double = 1.0

        enum CodingKeys: String, CodingKey {
            case id
            case startTS = "start_ts"
            case peakTS = "peak_ts"
            case endTS = "end_ts"
            case confidence
        }
    }

    struct TimeSpan: Codable, Identifiable {
        var id = UUID()
        var startTS: Double
        var endTS: Double

        enum CodingKeys: String, CodingKey {
            case startTS = "start_ts"
            case endTS = "end_ts"
        }
    }

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case sessionID = "session_id"
        case verified
        case reviewer
        case reviewedAt = "reviewed_at"
        case addedChews = "added_chews"
        case deletedChewIDs = "deleted_chew_ids"
        case editedChews = "edited_chews"
        case flippedEatingSpans = "flipped_eating_spans"
        case unreliableSpans = "unreliable_spans"
        case verifiedChewIDs = "verified_chew_ids"
        case notes
    }

    init(
        schemaVersion: String = "1.0.0",
        sessionID: String,
        verified: Bool,
        reviewer: String?,
        reviewedAt: String,
        addedChews: [ChewEdit],
        deletedChewIDs: [String],
        editedChews: [ChewEdit],
        flippedEatingSpans: [TimeSpan],
        unreliableSpans: [TimeSpan],
        verifiedChewIDs: [String] = [],
        notes: String?
    ) {
        self.schemaVersion = schemaVersion
        self.sessionID = sessionID
        self.verified = verified
        self.reviewer = reviewer
        self.reviewedAt = reviewedAt
        self.addedChews = addedChews
        self.deletedChewIDs = deletedChewIDs
        self.editedChews = editedChews
        self.flippedEatingSpans = flippedEatingSpans
        self.unreliableSpans = unreliableSpans
        self.verifiedChewIDs = verifiedChewIDs
        self.notes = notes
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        schemaVersion = try c.decodeIfPresent(String.self, forKey: .schemaVersion) ?? "1.0.0"
        sessionID = try c.decode(String.self, forKey: .sessionID)
        verified = try c.decodeIfPresent(Bool.self, forKey: .verified) ?? false
        reviewer = try c.decodeIfPresent(String.self, forKey: .reviewer)
        reviewedAt = try c.decodeIfPresent(String.self, forKey: .reviewedAt) ?? ""
        addedChews = try c.decodeIfPresent([ChewEdit].self, forKey: .addedChews) ?? []
        deletedChewIDs = try c.decodeIfPresent([String].self, forKey: .deletedChewIDs) ?? []
        editedChews = try c.decodeIfPresent([ChewEdit].self, forKey: .editedChews) ?? []
        flippedEatingSpans = try c.decodeIfPresent([TimeSpan].self, forKey: .flippedEatingSpans) ?? []
        unreliableSpans = try c.decodeIfPresent([TimeSpan].self, forKey: .unreliableSpans) ?? []
        verifiedChewIDs = try c.decodeIfPresent([String].self, forKey: .verifiedChewIDs) ?? []
        notes = try c.decodeIfPresent(String.self, forKey: .notes)
    }

    static func empty(sessionID: String) -> ReviewOverrides {
        ReviewOverrides(
            sessionID: sessionID,
            verified: false,
            reviewer: nil,
            reviewedAt: ISO8601DateFormatter().string(from: Date()),
            addedChews: [],
            deletedChewIDs: [],
            editedChews: [],
            flippedEatingSpans: [],
            unreliableSpans: [],
            verifiedChewIDs: [],
            notes: nil
        )
    }
}
