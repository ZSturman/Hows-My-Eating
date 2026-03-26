//
//  VideoEditorViewModel.swift
//  VideoTimelineTest
//
//  Created by Zachary Sturman on 11/13/25.
//

import Foundation
import SwiftUI
import AVFoundation
import AVKit
import UIKit
import Combine



final class VideoEditorViewModel: ObservableObject {
    @Published var player: AVPlayer
    @Published var currentTime: Double = 0
    @Published var duration: Double = 0
    @Published var thumbnails: [ThumbnailFrame] = []
    @Published var markers: [VideoMarker] = []
    @Published var selectedMarkerID: UUID?
    @Published var segments: [Segment] = []

    let framesVisible: Int = 15

    private var timeObserver: Any?
    private let asset: AVURLAsset
    private let imageGenerator: AVAssetImageGenerator
    private var frameDuration: Double
    private let markerStorageKey: String

    private var originalMarkers: [VideoMarker] = []
    private var boundCSVURL: URL?

    init(videoURL: URL) {
        self.asset = AVURLAsset(url: videoURL)
        let item = AVPlayerItem(asset: asset)
        self.player = AVPlayer(playerItem: item)

        self.imageGenerator = AVAssetImageGenerator(asset: asset)
        self.imageGenerator.appliesPreferredTrackTransform = true
        self.imageGenerator.maximumSize = CGSize(width: 160, height: 90)

        self.frameDuration = 1.0 / 30.0
        self.duration = 0
        self.markerStorageKey = "markers_\(videoURL.lastPathComponent)"

        Task {
            await self.loadVideoProperties()
        }

        loadMarkers()
        setupTimeObserver()
    }

    deinit {
        if let obs = timeObserver {
            player.removeTimeObserver(obs)
        }
    }

    // MARK: - Time Observer

    private func setupTimeObserver() {
        let interval = CMTime(seconds: 0.05, preferredTimescale: 600)
        timeObserver = player.addPeriodicTimeObserver(forInterval: interval, queue: .main) { [weak self] time in
            guard let self = self else { return }
            self.currentTime = CMTimeGetSeconds(time)
        }
    }

    // MARK: - Asset loading (duration, frame rate)

    private func loadVideoProperties() async {
        do {
            let tracks = try await asset.loadTracks(withMediaType: .video)
            if let videoTrack = tracks.first {
                let fps = try await videoTrack.load(.nominalFrameRate)
                let frameDuration = fps > 0 ? 1.0 / fps : 1.0 / 30.0
                await MainActor.run {
                    self.frameDuration = Double(frameDuration)
                }
            }
            let assetDuration = try await asset.load(.duration)
            await MainActor.run {
                self.duration = CMTimeGetSeconds(assetDuration)
                self.updateThumbnails()
            }
        } catch {
            // Keep defaults on failure
        }
    }


    // MARK: - Thumbnails

    func updateThumbnails() {
        let count = framesVisible
        let total = duration

        guard count > 0, total > 0 else {
            DispatchQueue.main.async {
                self.thumbnails = []
            }
            return
        }

        let sampleTimes: [Double]
        if count == 1 {
            sampleTimes = [total / 2.0]
        } else {
            sampleTimes = (0..<count).map { index in
                Double(index) * total / Double(count - 1)
            }
        }

        let generator = imageGenerator

        var newFrames: [ThumbnailFrame?] = Array(repeating: nil, count: count)
        let group = DispatchGroup()

        for (idx, seconds) in sampleTimes.enumerated() {
            let cmTime = CMTime(seconds: seconds, preferredTimescale: 600)
            group.enter()
            generator.generateCGImageAsynchronously(for: cmTime) { cgImage, _, _ in
                let image = cgImage.map { UIImage(cgImage: $0) }
                let frame = ThumbnailFrame(id: idx, time: cmTime, image: image)
                DispatchQueue.main.async {
                    newFrames[idx] = frame
                    group.leave()
                }
            }
        }

        group.notify(queue: .main) {
            self.thumbnails = newFrames.compactMap { $0 }
        }
    }

    // MARK: - Zoom / Scrub / Seek

    func changeZoom(withScale scale: CGFloat) {
        // Zooming is disabled; thumbnails are static.
    }

    func seek(to time: Double) {
        let clamped = min(max(time, 0.0), duration)
        let cm = CMTime(seconds: clamped, preferredTimescale: 600)
        player.seek(to: cm, toleranceBefore: .zero, toleranceAfter: .zero)
        currentTime = clamped
    }

    // MARK: - Markers

    var selectedMarker: VideoMarker? {
        markers.first { $0.id == selectedMarkerID }
    }

    func addMarkerAtCurrentTime() {
        guard duration > 0 else { return }
        let t = currentTime
        // Provisional kind; will be normalized after insert.
        let marker = VideoMarker(id: UUID(), time: t, kind: .startChewing)
        markers.append(marker)
        normalizeMarkerKinds()
        recomputeSegments()
        saveMarkers()
    }

    func updateMarker(_ marker: VideoMarker, to time: Double) {
        guard let idx = markers.firstIndex(where: { $0.id == marker.id }) else { return }
        let clamped = min(max(time, 0.0), duration)
        markers[idx].time = clamped
        normalizeMarkerKinds()
        recomputeSegments()
        saveMarkers()
    }

    func deleteMarker(_ marker: VideoMarker) {
        markers.removeAll { $0.id == marker.id }
        if selectedMarkerID == marker.id {
            selectedMarkerID = nil
        }

        normalizeMarkerKinds()
        recomputeSegments()
        saveMarkers()
    }

    // MARK: - Session control

    func completeEditing() {
        //print("[VideoEditor] completeEditing() called; markers=\(markers.count), segments=\(segments.count)")
        guard duration > 0 else {
            //print("[VideoEditor] completeEditing() early return: duration=\(duration)")
            return
        }
        recomputeSegments()
        saveMarkers()
        originalMarkers = markers
    }
    func cancelEdits() {
        markers = originalMarkers
        selectedMarkerID = nil
        recomputeSegments()
        saveMarkers()
    }

    func finishLater() {
        recomputeSegments()
        saveMarkers()
        originalMarkers = markers
    }

    // MARK: - Marker typing / segments

    // Ensure marker kinds alternate (Start, Stop, Start, Stop...) in chronological order.
    private func normalizeMarkerKinds() {
        markers.sort { $0.time < $1.time }
        for idx in markers.indices {
            markers[idx].kind = (idx % 2 == 0) ? .startChewing : .stopChewing
        }
    }

    private func recomputeSegments() {
        let sorted = markers.sorted { $0.time < $1.time }

        var newSegments: [Segment] = []
        var openStart: VideoMarker?

        for marker in sorted {
            switch marker.kind {
            case .startChewing:
                openStart = marker
            case .stopChewing:
                if let start = openStart, marker.time > start.time {
                    newSegments.append(
                        Segment(
                            startTime: start.time,
                            endTime: marker.time,
                            isChewing: true
                        )
                    )
                    openStart = nil
                }
            }
        }

        segments = newSegments
    }

    func chewingState(at time: Double) -> ChewingState {
        guard !markers.isEmpty else {
            return .notChewing
        }

        if let seg = segments.first(where: { time >= $0.startTime && time < $0.endTime }) {
            return seg.isChewing ? .chewing : .notChewing
        }

        return .notChewing
    }

    // Determine what the next marker kind should be if a marker is dropped at a given time.
    func nextMarkerKind(at time: Double) -> MarkerKind {
        // Count how many markers occur strictly before this time.
        let countBefore = markers.filter { $0.time < time }.count
        return (countBefore % 2 == 0) ? .startChewing : .stopChewing
    }
    
    // Convenience based on the current playback time.
    var nextMarkerKindAtCurrentTime: MarkerKind {
        nextMarkerKind(at: currentTime)
    }
    
    var hasUnclosedChewingSegment: Bool {
        // An odd number of markers means the last Start has no matching Stop.
        return markers.count % 2 == 1
    }

    var addMarkerButtonTitle: String {
        switch nextMarkerKindAtCurrentTime {
        case .startChewing:
            return "Start Chewing"
        case .stopChewing:
            return "Stop Chewing"
        }
    }
    
    // MARK: - CSV labelling

    /// Bind a CSV file whose `label` column should be kept in sync with the current markers.
    /// Call this once you know which CSV belongs to this video.
    func bindCSVForLabelling(_ url: URL) {
        //print("[VideoEditor] bindCSVForLabelling called with \(url.lastPathComponent)")
        boundCSVURL = url
        //print("[VideoEditor] bindCSVForLabelling: attempting initial relabel")
        try? updateLabelsInBoundCSV()
    }
    /// Re-run labelling on the currently bound CSV, if any.
    /// This is automatically called whenever markers are saved,
    /// but you may also call it manually if needed.
    func relabelBoundCSV() {
        try? updateLabelsInBoundCSV()
    }

    /// Core implementation that walks the CSV and fills the `label` column
    /// based on whether each timestamp falls inside a chewing segment.
    ///
    /// - Parameter csvURL: Path to the CSV file to update in-place.
    func relabelCSV(at csvURL: URL) throws {
        //print("[VideoEditor] relabelCSV(at:) started for \(csvURL.lastPathComponent)")

        let data = try Data(contentsOf: csvURL)
        guard var content = String(data: data, encoding: .utf8) else {
            //int("[VideoEditor] relabelCSV: failed to decode CSV as UTF-8")
            return
        }
        //print("[VideoEditor] relabelCSV: loaded CSV content (\(content.count) chars)")

        // If the CSV is completely empty, there is nothing to label.
        if content.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            //print("[VideoEditor] relabelCSV: CSV is empty, nothing to relabel")
            return
        }

        // Normalize line endings to `\n` for simpler processing.
        content = content
            .replacingOccurrences(of: "\r\n", with: "\n")
            .replacingOccurrences(of: "\r", with: "\n")

        var lines = content.components(separatedBy: "\n")
        if lines.count == 1 && lines[0].trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            //print("[VideoEditor] relabelCSV: no lines in CSV (only empty line)")
            return
        }

        // Parse header.
        let header = lines[0]
        var headerColumns = header
            .split(separator: ",", omittingEmptySubsequences: false)
            .map { String($0) }

        // Find or create timestamp and label columns.
        guard let timestampIndex = headerColumns.firstIndex(where: {
            $0.trimmingCharacters(in: .whitespacesAndNewlines).lowercased() == "timestamp"
        }) else {
            //print("[VideoEditor] relabelCSV: no 'timestamp' column in header: \(headerColumns)")
            return
        }

        var labelIndex = headerColumns.firstIndex(where: {
            $0.trimmingCharacters(in: .whitespacesAndNewlines).lowercased() == "label"
        })

        if labelIndex == nil {
            headerColumns.append("label")
            labelIndex = headerColumns.count - 1
        }

        //print("[VideoEditor] relabelCSV: timestampIndex=\(timestampIndex), labelIndex=\(labelIndex ?? -1)")

        lines[0] = headerColumns.joined(separator: ",")

        // Find the first non-empty, parsable timestamp from the data rows.
        var firstDataTimestamp: Double?
        for rowIndex in 1..<lines.count {
            let rawLine = lines[rowIndex].trimmingCharacters(in: .whitespacesAndNewlines)
            if rawLine.isEmpty { continue }
            let columns = rawLine
                .split(separator: ",", omittingEmptySubsequences: false)
                .map { String($0) }
            if timestampIndex < columns.count {
                let timestampString = columns[timestampIndex]
                    .trimmingCharacters(in: .whitespacesAndNewlines)
                if let t = Double(timestampString) {
                    firstDataTimestamp = t
                    break
                }
            }
        }

//        if let firstDataTimestamp {
//            print("[VideoEditor] relabelCSV: firstDataTimestamp=\(firstDataTimestamp)")
//        } else {
//            print("[VideoEditor] relabelCSV: no parsable data timestamp found; labels may remain unchanged")
//        }

        // Counters for debugging.
        var totalRows = 0
        var chewingRows = 0
        var nonChewingRows = 0
        var unparsableRows = 0

        // Process each data row.
        for rowIndex in 1..<lines.count {
            let rawLine = lines[rowIndex]
                .trimmingCharacters(in: .whitespacesAndNewlines)
            if rawLine.isEmpty {
                continue
            }

            totalRows += 1

            var columns = rawLine
                .split(separator: ",", omittingEmptySubsequences: false)
                .map { String($0) }

            // Make sure we have enough columns.
            if columns.count <= max(timestampIndex, labelIndex!) {
                columns += Array(
                    repeating: "",
                    count: max(timestampIndex, labelIndex!) - columns.count + 1
                )
            }

            let timestampString = columns[timestampIndex]
                .trimmingCharacters(in: .whitespacesAndNewlines)

            guard let timestamp = Double(timestampString) else {
                unparsableRows += 1
                //print("[VideoEditor] relabelCSV: unparsable timestamp at row \(rowIndex): '\(timestampString)'")
                lines[rowIndex] = columns.joined(separator: ",")
                continue
            }

            let base = firstDataTimestamp ?? timestamp
            let relativeTime = max(0, timestamp - base)
            let state = chewingState(at: relativeTime)
            let labelValue: String
            switch state {
            case .chewing:
                labelValue = "true"
                chewingRows += 1
            case .notChewing:
                labelValue = "false"
                nonChewingRows += 1
            }

//            if rowIndex <= 5 {
//                print("[VideoEditor] relabelCSV row \(rowIndex): timestamp=\(timestamp), base=\(base), relativeTime=\(relativeTime), state=\(state), labelValue=\(labelValue)")
//            }

            columns[labelIndex!] = labelValue
            lines[rowIndex] = columns.joined(separator: ",")
        }

        let updatedContent = lines.joined(separator: "\n")
        try updatedContent.write(to: csvURL, atomically: true, encoding: .utf8)

       // print("[VideoEditor] relabelCSV finished: totalRows=\(totalRows), chewingRows=\(chewingRows), nonChewingRows=\(nonChewingRows), unparsableRows=\(unparsableRows)")
    }

    /// Helper that updates labels in the currently bound CSV, if any.
    private func updateLabelsInBoundCSV() throws {
        //print("[VideoEditor] updateLabelsInBoundCSV() called")
        guard let url = boundCSVURL else {
            //print("[VideoEditor] updateLabelsInBoundCSV: no bound CSV URL")
            return
        }
       // print("[VideoEditor] updateLabelsInBoundCSV: bound URL = \(url.lastPathComponent)")
        try relabelCSV(at: url)
    }
    
    // MARK: - Persistence

    private struct MarkerDTO: Codable {
        let id: UUID
        let time: Double
        let kind: MarkerKind
    }

    private func saveMarkers() {
        //print("[VideoEditor] saveMarkers() called; markers=\(markers.count), segments=\(segments.count)")
        let dto = markers.map { MarkerDTO(id: $0.id, time: $0.time, kind: $0.kind) }
        if let data = try? JSONEncoder().encode(dto) {
            UserDefaults.standard.set(data, forKey: markerStorageKey)
        }
        // Whenever markers change, propagate the changes to the bound CSV (if any).
        do {
            try updateLabelsInBoundCSV()
        } catch {
            //print("[VideoEditor] saveMarkers() – updateLabelsInBoundCSV error: \(error)")
        }
    }
    
    private func loadMarkers() {
        if
            let data = UserDefaults.standard.data(forKey: markerStorageKey),
            let dto = try? JSONDecoder().decode([MarkerDTO].self, from: data)
        {
            self.markers = dto.map { VideoMarker(id: $0.id, time: $0.time, kind: $0.kind) }
        } else {
            self.markers = []
        }

        normalizeMarkerKinds()
        originalMarkers = markers

        recomputeSegments()
    }

    // MARK: - Formatting

    var formattedCurrentTime: String {
        formatTime(currentTime)
    }

    var formattedDuration: String {
        formatTime(duration)
    }

    private func formatTime(_ seconds: Double) -> String {
        guard seconds.isFinite && seconds >= 0 else { return "00:00:00" }
        let total = Int(seconds.rounded())
        let h = total / 3600
        let m = (total % 3600) / 60
        let s = total % 60
        return String(format: "%02d:%02d:%02d", h, m, s)
    }
}
