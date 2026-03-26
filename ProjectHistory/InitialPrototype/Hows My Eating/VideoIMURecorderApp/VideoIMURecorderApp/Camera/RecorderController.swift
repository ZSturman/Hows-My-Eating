//
//  RecorderController.swift
//  VideoIMURecorderApp
//
//  Created by Zachary Sturman on 9/7/25.
//

import Foundation
import AVFoundation
import Combine
import CoreMotion

struct RecordingMetadata: Codable {
    var labelled: Bool
    var shared: Bool
}

final class RecorderController: NSObject, ObservableObject {
    // Exposed to UI
    @Published var isRecording = false
    @Published var isPaused = false
    @Published var canResumeRecording = false
    
    @Published var statusText = "Idle"
    @Published var alert: AppAlert?
    @Published var isMotionAvailable: Bool = false

    @Published var latestMotion: (ax: Double, ay: Double, az: Double)?

    // Capture session to show live preview (owned by VideoIMURecorder internally)
    @Published var captureSession: AVCaptureSession?

    // Last recorded file URL (in app’s tmp, then moved)
    @Published var lastURL: URL?
    @Published var lastSessionFolder: URL?   // Folder where the current session files are saved (named by label prefix)
    
    @Published private(set) var sessionMetadata: [String: RecordingMetadata] = [:]
    private let metadataDefaultsKey = "RecordingSessionMetadata"
    private var currentEatingLabel: Bool?

    private var recorder: VideoIMURecorder?
    private var cancellables = Set<AnyCancellable>()
    private var imuCheckTimer: DispatchSourceTimer?

    override init() {
        super.init()
        loadMetadata()
    }

    func activateAudioSession() {
        let audio = AVAudioSession.sharedInstance()
        do {
            try audio.setCategory(.playback, options: [.mixWithOthers])
            try audio.setActive(true)
        } catch {
            print("Failed to activate audio session: \(error)")
        }
    }

    private func makeTimestampString() -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyyMMdd-HHmmss"
        formatter.locale = Locale(identifier: "en_US_POSIX")
        return formatter.string(from: Date())
    }

    func prepare() {
        Task { @MainActor in
            do {
                try await requestPermissions()
                self.activateAudioSession()
                if self.recorder == nil {
                    let tmp = FileManager.default.temporaryDirectory.appendingPathComponent("warmup.mov")
                    let r = VideoIMURecorder(outputURL: tmp)
                    
                    r.onError = { [weak self] err in
                        DispatchQueue.main.async { self?.alert = AppAlert("Recorder error", err.localizedDescription) }
                    }
                    try r.configureSessionOnly()
                    self.recorder = r
                    self.captureSession = r.exposedSession
                    r.startPreview()
                    
                    r.trialDeviceMotionCheck { [weak self] ready in
                        DispatchQueue.main.async {
                            self?.isMotionAvailable = ready
                        }
                    }
                    
                    let publisher = r.publisher(for: \.isMotionAvailable, options: [.initial, .new])
                        .receive(on: DispatchQueue.main)
                        .sink { [weak self] available in
                            guard let self = self else { return }
                            self.handleMotionAvailabilityChange(available)
                        }
                    self.cancellables.insert(publisher)
                    
                    // New: Setup deviceMotion update handler to update latestMotion
                    r.deviceMotionHandler = { [weak self] deviceMotion in
                        guard let dm = deviceMotion else {
                            DispatchQueue.main.async {
                                self?.latestMotion = nil
                            }
                            return
                        }
                        let ax = dm.userAcceleration.x
                        let ay = dm.userAcceleration.y
                        let az = dm.userAcceleration.z
                        DispatchQueue.main.async {
                            self?.latestMotion = (ax, ay, az)
                        }
                    }
                }
                
                imuCheckTimer?.cancel()
                let timer = DispatchSource.makeTimerSource(queue: DispatchQueue.global(qos: .userInitiated))
                timer.schedule(deadline: .now(), repeating: 2.5)
                timer.setEventHandler { [weak self] in self?.checkIMUReadiness() }
                timer.resume()
                imuCheckTimer = timer

                statusText = "Ready"
            } catch {
                alert = AppAlert("Permissions needed", error.localizedDescription)
            }
        }
    }
    
    func startCameraPreview() {
        recorder?.startPreview()
    }

    func stopCameraPreview() {
        recorder?.stopPreview()
    }
    
    func checkIMUReadiness() {
        recorder?.trialDeviceMotionCheck { [weak self] ready in
            DispatchQueue.main.async {
                self?.isMotionAvailable = ready
            }
        }
    }
    
    private func handleMotionAvailabilityChange(_ available: Bool) {
        isMotionAvailable = available

        if isRecording && !available {
            // Motion disappeared during an active recording: pause.
            pauseDueToMotionLoss()
        } else if isPaused && available {
            // Motion has come back while we are in paused state:
            // allow the user to resume.
            canResumeRecording = true
        }
    }

    func start(withLabel label: Bool?) {
        guard !isRecording else { return }
        guard let r = recorder else {
            alert = AppAlert("Not ready", "Recorder is not initialized yet.")
            return
        }

        currentEatingLabel = label

        let timestamp = makeTimestampString()
        // Determine base name prefix based on label semantics
        // "Eating" if true, "Not-eating" if false, "Session" if nil
        let basePrefix: String
        if let lbl = label {
            basePrefix = lbl ? "Eating" : "Not-eating"
        } else {
            basePrefix = "Session"
        }
        let baseName = "\(basePrefix)-\(timestamp)"
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
        let folder = docs.appendingPathComponent(baseName, isDirectory: true)
        try? FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)

        let videoName = "\(baseName).mov"
        let url = folder.appendingPathComponent(videoName)

        // Set recording label for events
        r.recordingLabel = label

        // Start recording
        r.startRecording(to: url)

        self.isRecording = true
        self.statusText = "Recording…"
        self.lastURL = nil
        self.lastSessionFolder = folder
    }

    func start() {
        start(withLabel: nil)
    }

    func stop() {
        guard isRecording, let r = recorder else { return }
        // Flip immediately so UI can't call stop again
        isRecording = false
        statusText = "Finishing…"
        r.stop { [weak self] in
            DispatchQueue.main.async {
                guard let self else { return }
                self.statusText = "Saved"
                let url = r.outputURL
                self.lastURL = url
                self.lastSessionFolder = url.deletingLastPathComponent()
                if let folder = self.lastSessionFolder {
                    let isEating = self.currentEatingLabel ?? false
                    let labelledValue = !isEating   // Not Eating -> labelled = true, Eating -> labelled = false
                    self.setMetadata(for: folder, labelled: labelledValue, shared: false)
                    self.currentEatingLabel = nil
                    // Force a directory refresh by briefly touching the folder; ShareLink reads a fresh listing.
                    _ = try? FileManager.default.contentsOfDirectory(at: folder, includingPropertiesForKeys: nil)
                    // Create/refresh a zip archive for this session to simplify sharing
                    _ = try? self.zipSessionFolder(folder)
                }
            }
        }
    }
    
    /// Automatically invoked when IMU data becomes unavailable during an active recording.
    private func pauseDueToMotionLoss() {
        guard isRecording, let r = recorder else { return }

        // Flip flags so the UI enters the paused state.
        isRecording = false
        isPaused = true
        canResumeRecording = false
        statusText = "Paused – lost motion data"

        r.stop { [weak self] in
            DispatchQueue.main.async {
                guard let self else { return }

                self.statusText = "Paused – saved partial segment"

                let url = r.outputURL
                self.lastURL = url
                self.lastSessionFolder = url.deletingLastPathComponent()

                // Preserve currentEatingLabel so we can reuse it on resume,
                // but still record metadata for this partial segment.
                if let folder = self.lastSessionFolder {
                    let isEating = self.currentEatingLabel ?? false
                    let labelledValue = !isEating   // Not Eating -> labelled = true, Eating -> labelled = false
                    self.setMetadata(for: folder, labelled: labelledValue, shared: false)
                    // Note: do NOT clear currentEatingLabel here.
                }
            }
        }
    }

    /// Called when the user decides they are done after a pause.
    func cancelPausedRecording() {
        isPaused = false
        canResumeRecording = false
        currentEatingLabel = nil
        statusText = "Cancelled"
        // We do not delete the partial recording; it remains as its own session.
    }

    /// Called when the user taps Resume after motion becomes available again.
    func resumeAfterMotionReturns() {
        guard isPaused, isMotionAvailable, canResumeRecording else { return }
        isPaused = false
        canResumeRecording = false
        statusText = "Resuming…"

        // Resume with the same "Eating"/"Not Eating" choice as before.
        start(withLabel: currentEatingLabel)
    }


    // MARK: - Permissions
    private func requestPermissions() async throws {
        // Camera
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized: break
        case .notDetermined:
            let ok = await AVCaptureDevice.requestAccess(for: .video)
            if !ok { throw Err("Camera access denied") }
        default:
            throw Err("Camera access denied")
        }
        // Headphone motion prompts when starting the manager; no preflight API needed.
    }

    // MARK: - Sessions folder helpers

    func allSessionFolders() -> [URL] {
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
        let contents = (try? FileManager.default.contentsOfDirectory(at: docs, includingPropertiesForKeys: [.creationDateKey], options: .skipsHiddenFiles)) ?? []
        let sessionFolders = contents.filter { url in
            var isDir: ObjCBool = false
            guard FileManager.default.fileExists(atPath: url.path, isDirectory: &isDir),
                  isDir.boolValue else {
                return false
            }
            let name = url.lastPathComponent
            return !name.hasPrefix(".")
        }
        return sessionFolders.sorted { lhs, rhs in
            let lhsDate = (try? lhs.resourceValues(forKeys: [.creationDateKey]).creationDate) ?? Date.distantPast
            let rhsDate = (try? rhs.resourceValues(forKeys: [.creationDateKey]).creationDate) ?? Date.distantPast
            return lhsDate > rhsDate
        }
    }

    /// Deletes the given session folder and all its contents.
    func deleteSessionFolder(_ url: URL) {
        try? FileManager.default.removeItem(at: url)
        sessionMetadata.removeValue(forKey: url.lastPathComponent)
        persistMetadata()
    }

    @discardableResult
        func zipSessionFolder(_ folder: URL) throws -> URL {
            // Note: Foundation does not provide a built-in ZIP API like `FileManager.zipItem`.
            // If you need real zipping, consider adding a third-party library (e.g., ZIPFoundation),
            // or implement your own archiving using Compression/Archive. For now, we safely fall back
            // to returning the folder itself so callers can still share the session contents.
            //
            // Previous (invalid) behavior attempted to create `folder.zip`. That API does not exist.
            // Returning the folder avoids creating a misleading URL to a non-existent file.
            return folder
        }

    private func loadMetadata() {
        guard let data = UserDefaults.standard.data(forKey: metadataDefaultsKey) else { return }
        if let decoded = try? JSONDecoder().decode([String: RecordingMetadata].self, from: data) {
            sessionMetadata = decoded
        }
    }

    private func persistMetadata() {
        if let data = try? JSONEncoder().encode(sessionMetadata) {
            UserDefaults.standard.set(data, forKey: metadataDefaultsKey)
        }
    }

    private func setMetadata(for folder: URL, labelled: Bool, shared: Bool) {
        let key = folder.lastPathComponent
        sessionMetadata[key] = RecordingMetadata(labelled: labelled, shared: shared)
        persistMetadata()
    }

    func metadata(for folder: URL) -> RecordingMetadata? {
        let key = folder.lastPathComponent
        return sessionMetadata[key]
    }

    func markShared(for folder: URL) {
        let key = folder.lastPathComponent
        var meta = sessionMetadata[key] ?? RecordingMetadata(labelled: false, shared: false)
        meta.shared = true
        sessionMetadata[key] = meta
        persistMetadata()
    }

    func markShared(for folders: [URL]) {
        for folder in folders {
            markShared(for: folder)
        }
    }

    /// Updates the `labelled` flag for the given session folder while preserving the current `shared` value.
    func setLabelled(_ labelled: Bool, for folder: URL) {
        let key = folder.lastPathComponent
        var meta = sessionMetadata[key] ?? RecordingMetadata(labelled: false, shared: false)
        meta.labelled = labelled
        sessionMetadata[key] = meta
        persistMetadata()
    }

    deinit {
        imuCheckTimer?.cancel()
        imuCheckTimer = nil
    }

}

// MARK: - Small alert type
struct AppAlert: Identifiable {
    let id = UUID()
    let title: String
    let message: String
    init(_ title: String, _ message: String) { self.title = title; self.message = message }
}
struct Err: LocalizedError { let message: String; init(_ m:String){message=m}; var errorDescription:String?{message} }
