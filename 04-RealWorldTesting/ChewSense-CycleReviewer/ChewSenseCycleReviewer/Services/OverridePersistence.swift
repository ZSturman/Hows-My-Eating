import Foundation

enum OverridePersistence {
    static func save(_ overrides: ReviewOverrides, session: Session, mergedRows: [AlignedLabel]) throws {
        let fm = FileManager.default

        let snapshot = session.derivedDir.appending(path: "motion_aligned_labels.auto.csv")
        if !fm.fileExists(atPath: snapshot.path), fm.fileExists(atPath: session.alignedCSV.path) {
            try fm.copyItem(at: session.alignedCSV, to: snapshot)
        }

        try fm.createDirectory(at: session.rawDir, withIntermediateDirectories: true)
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes]
        let data = try encoder.encode(overrides)
        try data.write(to: session.overridesURL, options: .atomic)

        try CSVLoader.writeAlignedLabels(mergedRows, to: session.alignedCSV)
    }

    static func loadIfPresent(_ url: URL) -> ReviewOverrides? {
        guard FileManager.default.fileExists(atPath: url.path),
              let data = try? Data(contentsOf: url) else { return nil }
        return try? JSONDecoder().decode(ReviewOverrides.self, from: data)
    }
}
