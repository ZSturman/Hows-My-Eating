//
//  RecordingDetailView.swift
//  VideoIMURecorderApp
//
//  Created by Zachary Sturman on 11/12/25.
//

import SwiftUI
import AVFoundation
import AVKit


struct RecordingDetailView: View {
    @StateObject private var viewModel: VideoEditorViewModel
    @State private var validationMessage: String?
    
    @EnvironmentObject var recorderController: RecorderController
    @State private var showShareSheet = false
    @State private var itemsToShare: [URL] = []
    @State private var isLabelled: Bool = false
    @State private var isShared: Bool = false
    @State private var selectedMovURL: URL?
    @State private var hasValidCSV: Bool = true
    
    let folder: URL
    
    init(folder: URL) {
        self.folder = folder

        let files = (try? FileManager.default.contentsOfDirectory(at: folder, includingPropertiesForKeys: nil)) ?? []
        guard let movURL = files.first(where: { $0.pathExtension.lowercased() == "mov" }) else {
            fatalError("No .mov file found in folder \(folder)")
        }

        // Create the view model for the video
        let vm = VideoEditorViewModel(videoURL: movURL)

        // Check for a valid CSV file: exists and non-zero size
        var validCSV = false
        if let csvURL = files.first(where: { $0.pathExtension.lowercased() == "csv" }) {
            if let attrs = try? FileManager.default.attributesOfItem(atPath: csvURL.path),
               let size = attrs[.size] as? NSNumber,
               size.intValue > 0 {
                vm.bindCSVForLabelling(csvURL)
                validCSV = true
            }
        }

        _viewModel = StateObject(wrappedValue: vm)
        self._selectedMovURL = State(initialValue: movURL)
        self._hasValidCSV = State(initialValue: validCSV)
    }

    private var parsedTitle: String {
        // Expecting folder or file name like "Eating-YYYYMMDD-HHmmss.*" or "Not-eating-YYYYMMDD-HHmmss.*"
        let name = selectedMovURL?.deletingPathExtension().lastPathComponent ?? folder.lastPathComponent
        if name.hasPrefix("Eating-") { return "Eating" }
        if name.hasPrefix("Not-eating-") { return "Not Eating" }
        // Fallback to first component before dash
        if let first = name.split(separator: "-").first { return first.replacingOccurrences(of: "-", with: " ") }
        return name
    }

    private var parsedDate: Date? {
        // Extract the timestamp part after the first dash
        let name = selectedMovURL?.deletingPathExtension().lastPathComponent ?? folder.lastPathComponent
        guard let dashRange = name.range(of: "-") else { return nil }
        let ts = String(name[dashRange.upperBound...])
        // ts is like "yyyyMMdd-HHmmss" possibly with additional suffixes; take first 15 chars
        let trimmed = String(ts.prefix(15))
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyyMMdd-HHmmss"
        formatter.locale = Locale(identifier: "en_US_POSIX")
        return formatter.date(from: trimmed)
    }

    private var relativeSubtitle: String {
        guard let date = parsedDate else { return "" }
        return date.formatted(.relative(presentation: .named))
    }

    private func refreshMetadata() {
        if let meta = recorderController.metadata(for: folder) {
            isLabelled = meta.labelled
            isShared = meta.shared
        } else {
            isLabelled = false
            isShared = false
        }
    }

    private func prepareShareItems() {
        // Prefer zip if available; fallback to folder contents
        if #available(iOS 16.0, *) {
            if let zip = try? recorderController.zipSessionFolder(folder) {
                itemsToShare = [zip]
                return
            }
        }
        itemsToShare = (try? FileManager.default.contentsOfDirectory(at: folder, includingPropertiesForKeys: nil)) ?? []
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 12) {

                // Video playback view
                PlainVideoPlayerView(player: viewModel.player)
                    .aspectRatio(16.0 / 9.0, contentMode: .fit)

                // Centered play/pause button between video and timeline
                Button(action: togglePlayPause) {
                    Image(systemName: viewModel.player.timeControlStatus == .playing ? "pause.fill" : "play.fill")
                        .font(.largeTitle)
                }
                .frame(maxWidth: .infinity)

                // Time labels
                HStack {
                    Text(viewModel.formattedCurrentTime)
                        .font(.caption)
                        .monospacedDigit()

                    Spacer()

                    Text(viewModel.formattedDuration)
                        .font(.caption)
                        .monospacedDigit()
                }
                .padding(.horizontal)

                // Show warning if no valid CSV is present
                if !hasValidCSV {
                    Text("No motion CSV was recorded for this session. Labelling will not be written to a CSV.")
                        .font(.footnote)
                        .foregroundColor(.red)
                        .padding(.horizontal)
                }

                // Timeline scrubber with thumbnails and markers
                TimelineView(viewModel: viewModel, markersEnabled: !isLabelled && hasValidCSV)
                    .frame(height: 100)
                    .padding(.horizontal)
                    // Deselect selected marker when tapping outside
                    .contentShape(Rectangle())
                    .onTapGesture {
                        viewModel.selectedMarkerID = nil
                    }

                // Marker controls: Previous, Primary, Next
                MarkerControls(
                    isLabelled: isLabelled || !hasValidCSV,
                    primaryTitle: primaryButtonTitle,
                    onPrevious: goToPreviousMarker,
                    onPrimary: primaryAction,
                    onNext: goToNextMarker
                )
                .padding(.horizontal)

                // Conditional share/edit area
                Group {
                    if !hasValidCSV {
                        Text("This recording has no motion CSV. You can watch the video, but labelling and export are unavailable.")
                            .font(.footnote)
                            .foregroundColor(.red)
                    } else if !isLabelled {
                        VStack(spacing: 12) {
                            Button("Labelling finished") {
                                viewModel.completeEditing()
                                validationMessage = nil
                                // Mark as labelled when done
                                recorderController.setLabelled(true, for: folder)
                                refreshMetadata()
                            }
                            .disabled(viewModel.hasUnclosedChewingSegment)
                            .simultaneousGesture(
                                TapGesture().onEnded {
                                    if viewModel.hasUnclosedChewingSegment {
                                        validationMessage = "Please add a Stop Chewing marker to close the current chewing segment before finishing."
                                    } else {
                                        validationMessage = nil
                                    }
                                }
                            )
                            
                            Button("Finish later") {
                                viewModel.finishLater()
                                validationMessage = nil
                            }
                        }
                    } else if isLabelled && !isShared {
                        VStack(spacing: 12) {
                            Button {
                                prepareShareItems()
                                showShareSheet = true
                            } label: {
                                Label("Share", systemImage: "square.and.arrow.up")
                            }
                            .buttonStyle(.borderedProminent)

                            Button("Edit labels") {
                                recorderController.setLabelled(false, for: folder)
                                refreshMetadata()
                            }
                            .buttonStyle(.bordered)
                        }
                    } else if isLabelled && isShared {
                        VStack(spacing: 8) {
                            Text("Shared successfully")
                                .font(.footnote)
                                .foregroundStyle(.green)
                            HStack(spacing: 12) {
                                Button {
                                    prepareShareItems()
                                    showShareSheet = true
                                } label: {
                                    Label("Share Again", systemImage: "square.and.arrow.up")
                                }
                                .buttonStyle(.borderedProminent)

                                Button("Edit labels") {
                                    recorderController.setLabelled(false, for: folder)
                                    refreshMetadata()
                                }
                                .buttonStyle(.bordered)
                            }
                        }
                    }
                }
                .padding(.top, 8)

                if let validationMessage {
                    Text(validationMessage)
                        .font(.footnote)
                        .foregroundColor(.red)
                        .padding(.bottom, 8)
                }

                Spacer(minLength: 8)
            }
            .toolbar {
                ToolbarItem(placement: .principal) {
                    VStack(spacing: 0) {
                        Text(parsedTitle).font(.headline)
                        if !relativeSubtitle.isEmpty {
                            Text(relativeSubtitle).font(.caption).foregroundStyle(.secondary)
                        }
                    }
                }
            }
            .onChange(of: viewModel.hasUnclosedChewingSegment) { _, newValue in
                if !newValue {
                    validationMessage = nil
                }
            }
            .onAppear {
                refreshMetadata()
            }
            .sheet(isPresented: $showShareSheet, onDismiss: {
                itemsToShare = []
                refreshMetadata()
            }) {
                if !itemsToShare.isEmpty {
                    ActivityView(activityItems: itemsToShare) { completed in
                        if completed {
                            recorderController.markShared(for: folder)
                            refreshMetadata()
                        }
                    }
                }
            }
        }
        .navigationTitle("")
        .navigationBarTitleDisplayMode(.inline)
    }
    
    private var primaryButtonTitle: String {
        if viewModel.selectedMarker != nil { return "Delete Marker" }
        return viewModel.addMarkerButtonTitle
    }

    private func primaryAction() {
        if let marker = viewModel.selectedMarker {
            viewModel.deleteMarker(marker)
        } else {
            viewModel.addMarkerAtCurrentTime()
        }
    }

    private func goToPreviousMarker() {
        let t = viewModel.currentTime
        let prior = viewModel.markers.filter { $0.time < t }.max(by: { $0.time < $1.time })
        if let m = prior {
            viewModel.seek(to: m.time)
        } else {
            viewModel.seek(to: 0)
        }
    }

    private func goToNextMarker() {
        let t = viewModel.currentTime
        let next = viewModel.markers.filter { $0.time > t }.min(by: { $0.time < $1.time })
        if let m = next {
            viewModel.seek(to: m.time)
        } else {
            viewModel.seek(to: viewModel.duration)
        }
    }
    
    private func togglePlayPause() {
        if viewModel.player.timeControlStatus == .playing {
            viewModel.player.pause()
        } else {
            viewModel.player.play()
        }
    }
}

struct MarkerControls: View {
    var isLabelled: Bool
    var primaryTitle: String
    var onPrevious: () -> Void
    var onPrimary: () -> Void
    var onNext: () -> Void

    var body: some View {
        HStack(spacing: 16) {
            Button(action: onPrevious) {
                Image(systemName: "backward.end.alt")
                    .font(.title2)
            }
            .disabled(isLabelled)

            Button(primaryTitle) {
                onPrimary()
            }
            .buttonStyle(.borderedProminent)
            .disabled(isLabelled)

            Button(action: onNext) {
                Image(systemName: "forward.end.alt")
                    .font(.title2)
            }
            .disabled(isLabelled)
        }
    }
}
