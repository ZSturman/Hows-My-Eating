// RecordingsListView.swift
// Shows a list of all saved recording sessions, allows sharing or deleting individual or all sessions.

import SwiftUI
import AVFoundation
import AVKit

struct RecordingsListView: View {
    @ObservedObject var controller: RecorderController
    @Binding var selectedFolder: URL?
    @State private var showDeleteAllAlert = false
    @State private var selectedSession: URL?
    @State private var showShareSheet = false
    @State private var itemsToShare: [URL] = []

    var sessionFolders: [URL] {
        controller.allSessionFolders()
    }
    
    private func zipForFolder(_ folder: URL) -> URL? {
        if #available(iOS 16.0, *) {
            return try? controller.zipSessionFolder(folder)
        } else {
            // Fallback: return nil to share raw files
            return nil
        }
    }
    
    private var labelledFolders: [URL] {
        sessionFolders.filter { folder in
            if let meta = controller.metadata(for: folder) {
                return meta.labelled && !meta.shared
            } else {
                return false
            }
        }
    }

    private var unlabelledFolders: [URL] {
        sessionFolders.filter { folder in
            if let meta = controller.metadata(for: folder) {
                return !meta.labelled && !meta.shared
            } else {
                // Folders without metadata are treated as not labelled and not shared
                return true
            }
        }
    }

    private var sharedFolders: [URL] {
        sessionFolders.filter { folder in
            if let meta = controller.metadata(for: folder) {
                return meta.shared
            } else {
                return false
            }
        }
    }

    var body: some View {
        VStack {
            if sessionFolders.isEmpty {
                VStack(spacing: 12) {
                    
                    
                    Text("No recordings found.")
                        .foregroundStyle(.secondary)
                    NavigationLink(destination: CameraScreen(controller: controller)) {
                        HStack {
                            Image(systemName: "plus")
                            VStack(alignment: .leading) {
                                Text("New")
                                    .font(.body)
                            }
                        }
                    }
                }
            } else {
                List(selection: $selectedFolder) {
                    
                    
                    
                    Section("Not Labelled") {
                        ForEach(unlabelledFolders, id: \.self) { folder in
                            HStack {
                                Image(systemName: "video")
                                VStack(alignment: .leading) {
                                    Text(folder.lastPathComponent)
                                        .font(.body)
                                    if let attrs = try? FileManager.default.attributesOfItem(atPath: folder.path),
                                       let date = attrs[.creationDate] as? Date {
                                        Text(date.formatted(.dateTime))
                                            .font(.caption2)
                                            .foregroundStyle(.secondary)
                                    }
                                }
                            }
                            .tag(folder)
                            .swipeActions {
                                Button {
                                    selectedSession = folder
                                    if let zip = zipForFolder(folder) {
                                        itemsToShare = [zip]
                                    } else {
                                        itemsToShare = (try? FileManager.default.contentsOfDirectory(at: folder, includingPropertiesForKeys: nil)) ?? []
                                    }
                                    showShareSheet = true
                                } label: {
                                    Label("Share", systemImage: "square.and.arrow.up")
                                }
                                .tint(.blue)
                                Button(role: .destructive) {
                                    if selectedFolder == folder {
                                        selectedFolder = nil
                                    }
                                    controller.deleteSessionFolder(folder)
                                } label: {
                                    Label("Delete", systemImage: "trash")
                                }
                            }
                            .contextMenu {
                                Button {
                                    selectedSession = folder
                                    if let zip = zipForFolder(folder) {
                                        itemsToShare = [zip]
                                    } else {
                                        itemsToShare = (try? FileManager.default.contentsOfDirectory(at: folder, includingPropertiesForKeys: nil)) ?? []
                                    }
                                    showShareSheet = true
                                } label: {
                                    Label("Share", systemImage: "square.and.arrow.up")
                                }
                                Button(role: .destructive) {
                                    if selectedFolder == folder {
                                        selectedFolder = nil
                                    }
                                    controller.deleteSessionFolder(folder)
                                } label: {
                                    Label("Delete", systemImage: "trash")
                                }
                            }
                        }
                    }
                    Section("Labelled") {
                        ForEach(labelledFolders, id: \.self) { folder in
                            HStack {
                                Button(action: {
                                    selectedSession = folder
                                    if let zip = zipForFolder(folder) {
                                        itemsToShare = [zip]
                                    } else {
                                        itemsToShare = (try? FileManager.default.contentsOfDirectory(at: folder, includingPropertiesForKeys: nil)) ?? []
                                    }
                                    showShareSheet = true
                                }) {
                                    Label("Share", systemImage: "square.and.arrow.up")
                                }
                                .buttonStyle(.bordered)
                                
                                VStack(alignment: .leading) {
                                    Text(folder.lastPathComponent)
                                        .font(.body)
                                    if let attrs = try? FileManager.default.attributesOfItem(atPath: folder.path),
                                       let date = attrs[.creationDate] as? Date {
                                        Text(date.formatted(.dateTime))
                                            .font(.caption2)
                                            .foregroundStyle(.secondary)
                                    }
                                }
                                Spacer()
                            }
                            .tag(folder)
                            .swipeActions {
                                Button {
                                    selectedSession = folder
                                    if let zip = zipForFolder(folder) {
                                        itemsToShare = [zip]
                                    } else {
                                        itemsToShare = (try? FileManager.default.contentsOfDirectory(at: folder, includingPropertiesForKeys: nil)) ?? []
                                    }
                                    showShareSheet = true
                                } label: {
                                    Label("Share", systemImage: "square.and.arrow.up")
                                }
                                .tint(.blue)
                                Button(role: .destructive) {
                                    if selectedFolder == folder {
                                        selectedFolder = nil
                                    }
                                    controller.deleteSessionFolder(folder)
                                } label: {
                                    Label("Delete", systemImage: "trash")
                                }
                            }
                            .contextMenu {
                                Button {
                                    selectedSession = folder
                                    if let zip = zipForFolder(folder) {
                                        itemsToShare = [zip]
                                    } else {
                                        itemsToShare = (try? FileManager.default.contentsOfDirectory(at: folder, includingPropertiesForKeys: nil)) ?? []
                                    }
                                    showShareSheet = true
                                } label: {
                                    Label("Share", systemImage: "square.and.arrow.up")
                                }
                                Button(role: .destructive) {
                                    if selectedFolder == folder {
                                        selectedFolder = nil
                                    }
                                    controller.deleteSessionFolder(folder)
                                } label: {
                                    Label("Delete", systemImage: "trash")
                                }
                            }
                        }
                    }
                    Section("Shared") {
                        ForEach(sharedFolders, id: \.self) { folder in
                            HStack {
                                Image(systemName: "checkmark.circle")
                                VStack(alignment: .leading) {
                                    Text(folder.lastPathComponent)
                                        .font(.body)
                                    if let attrs = try? FileManager.default.attributesOfItem(atPath: folder.path),
                                       let date = attrs[.creationDate] as? Date {
                                        Text(date.formatted(.dateTime))
                                            .font(.caption2)
                                            .foregroundStyle(.secondary)
                                    }
                                }
                            }
                            .tag(folder)
                        }
                    }
                    Section {
                        Button(role: .destructive) {
                            selectedFolder = nil
                            showDeleteAllAlert = true
                        } label: {
                            Label("Delete All Recordings", systemImage: "trash")
                        }
                    }
                }
            }
        }
        .navigationTitle("Recordings")
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                if !sessionFolders.isEmpty {
                    Button(action: {
                        selectedSession = nil
                        var urls: [URL] = []
                        for f in sessionFolders {
                            if let zip = zipForFolder(f) {
                                urls.append(zip)
                            } else {
                                let files = (try? FileManager.default.contentsOfDirectory(at: f, includingPropertiesForKeys: nil)) ?? []
                                urls.append(contentsOf: files)
                            }
                        }
                        itemsToShare = urls
                        showShareSheet = true
                    }) {
                        Label("Share All", systemImage: "square.and.arrow.up")
                    }
                }
            }
        }
        .alert("Delete all recordings?", isPresented: $showDeleteAllAlert) {
            Button("Delete All", role: .destructive) {
                selectedFolder = nil
                sessionFolders.forEach { controller.deleteSessionFolder($0) }
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("This cannot be undone.")
        }
        .sheet(isPresented: $showShareSheet, onDismiss: {
            itemsToShare = []
        }) {
            if !itemsToShare.isEmpty {
                ActivityView(activityItems: itemsToShare) { completed in
                    if completed {
                        if let folder = selectedSession {
                            controller.markShared(for: folder)
                        } else {
                            controller.markShared(for: sessionFolders)
                        }
                    }
                }
            }
        }
    }
}
