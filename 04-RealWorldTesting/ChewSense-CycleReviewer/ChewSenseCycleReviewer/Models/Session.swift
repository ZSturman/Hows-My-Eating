import Foundation

/// Locates ChewSense workspace directories relative to a chosen project root.
struct WorkspacePaths {
    let root: URL

    var rawSessions: URL  { root.appending(path: "02-DataPipeline/data/raw_sessions") }
    var derivedRoot: URL  { root.appending(path: "02-DataPipeline/data/derived/video_labels") }

    func derived(for sessionID: String) -> URL { derivedRoot.appending(path: sessionID) }
    func raw(for sessionID: String) -> URL     { rawSessions.appending(path: sessionID) }
}

struct Session: Identifiable, Hashable {
    enum Status: String { case auto, inReview = "in-review", verified }

    let id: String
    let rawDir: URL
    let derivedDir: URL
    let videoURL: URL?
    let annotatedVideoURL: URL?
    let framePredictionsCSV: URL?
    let motionCSV: URL?
    let alignedCSV: URL
    let chewCyclesJSON: URL
    let overridesURL: URL
    let status: Status
}
