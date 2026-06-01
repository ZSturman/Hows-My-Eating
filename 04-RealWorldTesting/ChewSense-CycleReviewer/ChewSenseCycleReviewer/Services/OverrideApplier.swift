import Foundation

/// Applies a `ReviewOverrides` payload onto an array of auto-labels, returning
/// a fresh array suitable for writing back to disk. Mirrors the authoritative
/// Python implementation in `apply_review_overrides.py`.
enum OverrideApplier {
    static func apply(_ overrides: ReviewOverrides, to base: [AlignedLabel]) -> [AlignedLabel] {
        var rows = base

        let deletedIDs = Set(overrides.deletedChewIDs)
        if !deletedIDs.isEmpty {
            for i in rows.indices where deletedIDs.contains(rows[i].chewID) {
                rows[i].chewID = ""
                rows[i].chewPhase = "idle"
            }
        }

        let writes = overrides.addedChews + overrides.editedChews
        for chew in writes {
            for i in rows.indices where rows[i].chewID == chew.id {
                rows[i].chewID = ""
                rows[i].chewPhase = "idle"
            }
            for i in rows.indices {
                let t = rows[i].videoTS
                if t >= chew.startTS && t <= chew.peakTS {
                    rows[i].chewID = chew.id
                    rows[i].chewPhase = "opening"
                    rows[i].videoConfidence = chew.confidence
                } else if t > chew.peakTS && t <= chew.endTS {
                    rows[i].chewID = chew.id
                    rows[i].chewPhase = "closing"
                    rows[i].videoConfidence = chew.confidence
                }
            }
        }

        for span in overrides.flippedEatingSpans {
            for i in rows.indices {
                let t = rows[i].videoTS
                if t >= span.startTS && t <= span.endTS {
                    rows[i].eating = rows[i].eating == 1 ? 0 : 1
                }
            }
        }

        for span in overrides.unreliableSpans {
            for i in rows.indices {
                let t = rows[i].videoTS
                if t >= span.startTS && t <= span.endTS {
                    rows[i].chewPhase = "unreliable"
                    rows[i].chewID = ""
                }
            }
        }

        return rows
    }
}
