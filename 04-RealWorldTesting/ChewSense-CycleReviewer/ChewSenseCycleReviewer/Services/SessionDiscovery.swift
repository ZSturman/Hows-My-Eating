import Foundation

struct SessionDiscovery {
    let paths: WorkspacePaths
    private let fm = FileManager.default

    func listSessions() -> [Session] {
        guard let derivedContents = try? fm.contentsOfDirectory(
            at: paths.derivedRoot,
            includingPropertiesForKeys: [.isDirectoryKey],
            options: [.skipsHiddenFiles]
        ) else { return [] }

        var sessions: [Session] = []
        for derivedDir in derivedContents where (try? derivedDir.resourceValues(forKeys: [.isDirectoryKey]).isDirectory) == true {
            let sid = derivedDir.lastPathComponent
            let aligned = derivedDir.appending(path: "motion_aligned_labels.csv")
            let cycles = derivedDir.appending(path: "chew_cycles.json")
            guard fm.fileExists(atPath: aligned.path), fm.fileExists(atPath: cycles.path) else { continue }

            let rawDir = paths.raw(for: sid)
            let video = findFirst(in: rawDir, extensions: ["mov", "mp4", "MOV", "MP4"])
            let motion = findFirst(in: rawDir, extensions: ["csv"])
            let overridesURL = rawDir.appending(path: "review_overrides.json")
            let status = resolveStatus(overrides: overridesURL)

            let annotated = derivedDir.appending(path: "annotated_video.mp4")
            let annotatedURL = fm.fileExists(atPath: annotated.path) ? annotated : nil
            let framePreds = derivedDir.appending(path: "frame_predictions.csv")
            let framePredsURL = fm.fileExists(atPath: framePreds.path) ? framePreds : nil

            sessions.append(Session(
                id: sid,
                rawDir: rawDir,
                derivedDir: derivedDir,
                videoURL: video,
                annotatedVideoURL: annotatedURL,
                framePredictionsCSV: framePredsURL,
                motionCSV: motion,
                alignedCSV: aligned,
                chewCyclesJSON: cycles,
                overridesURL: overridesURL,
                status: status
            ))
        }
        return sessions.sorted { $0.id < $1.id }
    }

    private func findFirst(in dir: URL, extensions: [String]) -> URL? {
        guard let entries = try? fm.contentsOfDirectory(at: dir, includingPropertiesForKeys: nil) else { return nil }
        return entries.first { extensions.contains($0.pathExtension) }
    }

    private func resolveStatus(overrides: URL) -> Session.Status {
        guard fm.fileExists(atPath: overrides.path),
              let data = try? Data(contentsOf: overrides),
              let payload = try? JSONDecoder().decode(ReviewOverrides.self, from: data) else {
            return .auto
        }
        return payload.verified ? .verified : .inReview
    }
}
