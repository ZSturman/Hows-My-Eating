import Foundation

/// One row of `frame_predictions.csv` reduced to the fields the reviewer
/// needs for the cycle-shape graph: a video timestamp and a single
/// "mouth-open" magnitude. Pose-invariant `jaw_open_bs` (MediaPipe blendshape)
/// is preferred when present; falls back to `jaw_open_smooth`, then
/// `inner_lip_open`, then `jaw_open`.
struct FramePrediction {
    let ts: Double
    let mouthOpen: Double
}

enum FramePredictionsLoader {
    private static let preferredColumns = [
        "jaw_open_bs",
        "jaw_open_smooth",
        "inner_lip_open",
        "jaw_open",
    ]

    static func load(from url: URL) -> [FramePrediction] {
        guard let data = try? Data(contentsOf: url),
              let text = String(data: data, encoding: .utf8) else {
            return []
        }
        // Split into non-empty lines; tolerate \r\n.
        var lines = text.split(whereSeparator: \.isNewline)
        guard let headerLine = lines.first else { return [] }
        lines.removeFirst()

        let headers = parseCSVRow(String(headerLine))
        guard let tsIdx = headers.firstIndex(of: "ts") else { return [] }
        let openIdx: Int? = preferredColumns
            .lazy
            .compactMap { headers.firstIndex(of: $0) }
            .first
        guard let mouthIdx = openIdx else { return [] }

        var out: [FramePrediction] = []
        out.reserveCapacity(lines.count)
        for line in lines {
            let cols = parseCSVRow(String(line))
            if cols.count <= max(tsIdx, mouthIdx) { continue }
            guard let ts = Double(cols[tsIdx]),
                  let raw = Double(cols[mouthIdx]) else { continue }
            let mouth = raw.isFinite ? raw : 0
            out.append(FramePrediction(ts: ts, mouthOpen: mouth))
        }
        return out
    }

    /// Minimal CSV row parser. Handles double-quoted fields with embedded
    /// commas, but the pipeline never emits those for `frame_predictions.csv`
    /// — this is defensive only.
    private static func parseCSVRow(_ row: String) -> [String] {
        var fields: [String] = []
        var current = ""
        var inQuotes = false
        var iter = row.makeIterator()
        while let ch = iter.next() {
            if ch == "\"" {
                inQuotes.toggle()
            } else if ch == "," && !inQuotes {
                fields.append(current)
                current = ""
            } else {
                current.append(ch)
            }
        }
        fields.append(current)
        return fields
    }
}
