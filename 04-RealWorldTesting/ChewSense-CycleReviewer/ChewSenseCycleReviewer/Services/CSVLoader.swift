import Foundation

enum CSVLoader {
    static func loadAlignedLabels(from url: URL) throws -> [AlignedLabel] {
        let raw = try String(contentsOf: url, encoding: .utf8)
        var rows = raw.split(separator: "\n", omittingEmptySubsequences: true).map(String.init)
        guard !rows.isEmpty else { return [] }
        rows.removeFirst()

        var out: [AlignedLabel] = []
        out.reserveCapacity(rows.count)
        for (i, line) in rows.enumerated() {
            let cols = line.split(separator: ",", omittingEmptySubsequences: false).map(String.init)
            guard cols.count >= 6 else { continue }
            out.append(AlignedLabel(
                rowIndex: i,
                timestamp: Double(cols[0]) ?? 0,
                videoTS: Double(cols[1]) ?? 0,
                eating: Int(cols[2]) ?? 0,
                chewPhase: cols[3],
                chewID: cols[4],
                videoConfidence: Double(cols[5]) ?? 0
            ))
        }
        return out
    }

    static func writeAlignedLabels(_ rows: [AlignedLabel], to url: URL) throws {
        var text = AlignedLabel.csvHeader + "\n"
        text.reserveCapacity(rows.count * 64)
        for row in rows {
            text += row.toCSVRow()
            text += "\n"
        }
        try text.write(to: url, atomically: true, encoding: .utf8)
    }
}
