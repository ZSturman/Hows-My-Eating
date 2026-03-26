//
//  VideoIMURecorder.swift
//  VideoIMURecorderApp
//
//  Created by Zachary Sturman on 9/7/25.
//

import Foundation
import AVFoundation
import CoreMedia
import CoreMotion


/// Records a .mov with a video track + a timed-metadata track containing
/// 10 ms packets of AirPods IMU samples, keyed to the host clock.
final class VideoIMURecorder: NSObject, AVCaptureVideoDataOutputSampleBufferDelegate {
    // Public
    private(set) var outputURL: URL
    var onError: ((Error) -> Void)?
    /// Called with each new device motion sample (or nil if unavailable)
    var deviceMotionHandler: ((CMDeviceMotion?) -> Void)?
    var exposedSession: AVCaptureSession { session }
    /// Initial activity selection for the current recording (true = Eating, false = Not Eating).
    /// Used only after recording for CSV post-processing; motion events are saved without labels during capture.
    var recordingLabel: Bool? = nil
    
    @objc dynamic private(set) var isMotionAvailable: Bool = false
    private(set) var isRecording: Bool = false
    
    // Call this to build the AVCaptureSession without starting the writer yet.
    func configureSessionOnly() throws {
        try setupSession()
    }

    // Call this to run the preview without writing to disk.
    func startPreview() {
        if !session.isRunning {
            DispatchQueue.global(qos: .userInitiated).async { [weak self] in
                self?.session.startRunning()
            }
        }
    }

    func stopPreview() {
        if session.isRunning {
            DispatchQueue.global(qos: .userInitiated).async { [weak self] in
                self?.session.stopRunning()
            }
        }
    }

    func startRecording(to url: URL) {
        // Reuse the already-configured capture session; just point the writer at a new URL
        self.outputURL = url
        do {
            // Prepare CSV sidecar file
            let csvURL = url.deletingPathExtension().appendingPathExtension("csv")
            self.csvURL = csvURL
            FileManager.default.createFile(atPath: csvURL.path, contents: nil, attributes: nil)
            csvFileHandle = try FileHandle(forWritingTo: csvURL)

            // (Re)create the asset writer for the new URL
            try setupWriter()

            // Start motion capture batching
            setupMotion()
            startBatchTimer()

            // Make sure the session is running for both preview and capture
            if !session.isRunning {
                DispatchQueue.global(qos: .userInitiated).async { [weak self] in
                    self?.session.startRunning()
                }
            }
            isRecording = true
        } catch {
            onError?(error)
        }
    }
    
    func startRecording(to url: URL, isEating: Bool) {
        // Store the initial selection for post-processing; events are saved without labels during recording.
        self.recordingLabel = isEating
        startRecording(to: url)
    }

    // Private
    private let session = AVCaptureSession()
    private let videoOutput = AVCaptureVideoDataOutput()
    private var writer: AVAssetWriter!
    private var videoInput: AVAssetWriterInput!
    private let hmm = CMHeadphoneMotionManager()
    private let motionQueue = OperationQueue()

    // Batching
    private let batchWindowNs: UInt32 = 10_000_000 // 10 ms
    private var batchStartSeconds: Double?
    private var events: [MotionEvent] = []
    private var batchTimer: DispatchSourceTimer?
#if DEBUG
    // Print IMU samples to the Xcode console while recording. Set to 1 to print every sample,
    // or increase (e.g., 10) to throttle.
    private let debugPrintIMUSamplesEvery = 1
    private var debugIMUSampleCounter = 0
#endif

    // Time
    private let hostClock = CMClockGetHostTimeClock()
    private let hostTimescale: Int32 = 1_000_000_000 // ns

    private var csvFileHandle: FileHandle?
    private var csvURL: URL?

    private let videoWritingQueue = DispatchQueue(label: "video.writing.queue")
    
    private var motionAvailabilityTimer: DispatchSourceTimer?

    init(outputURL: URL) {
        self.outputURL = outputURL
        super.init()
        // Start timer to poll isDeviceMotionAvailable every 0.5s
        let timer = DispatchSource.makeTimerSource(queue: DispatchQueue.global(qos: .userInitiated))
        timer.schedule(deadline: .now(), repeating: .milliseconds(500))
        timer.setEventHandler { [weak self] in
            guard let self = self else { return }
            let available = self.hmm.isDeviceMotionAvailable
            if self.isMotionAvailable != available {
                DispatchQueue.main.async {
                    self.isMotionAvailable = available
                }
            }
        }
        timer.resume()
        motionAvailabilityTimer = timer
    }
    
    deinit {
        motionAvailabilityTimer?.cancel()
        motionAvailabilityTimer = nil
    }

    func start() {
        do {
            try setupSession()
            
            let csvURL = outputURL.deletingPathExtension().appendingPathExtension("csv")
            self.csvURL = csvURL
            FileManager.default.createFile(atPath: csvURL.path, contents: nil, attributes: nil)
            csvFileHandle = try FileHandle(forWritingTo: csvURL)
            
            try setupWriter()
            setupMotion()
            startBatchTimer()
            DispatchQueue.global(qos: .userInitiated).async { [weak self] in
                self?.session.startRunning()
            }
            isRecording = true
        } catch { onError?(error) }
    }

    func stop(completion: @escaping () -> Void) {
        // Prevent double-stop
        guard isRecording else {
            completion()
            return
        }
        isRecording = false

        // Flush any remaining IMU events before stopping timers and motion updates.
        flushBatch()

        batchTimer?.cancel()
        hmm.stopDeviceMotionUpdates()
        // Do not stop the session here; keep it running for preview
        // session.stopRunning()
        
        guard let writer = writer else {
            csvFileHandle?.closeFile()
            csvFileHandle = nil
            self.postprocessCSVIfNeeded()
            completion()
            return
        }
        
        switch writer.status {
        case .writing:
            videoInput?.markAsFinished()
            writer.finishWriting {
                self.csvFileHandle?.closeFile()
                self.csvFileHandle = nil
                self.postprocessCSVIfNeeded()
                completion()
            }
        default:
            writer.cancelWriting()
            csvFileHandle?.closeFile()
            csvFileHandle = nil
            self.postprocessCSVIfNeeded()
            completion()
        }
    }

    // MARK: Setup
    private func setupSession() throws {
        session.beginConfiguration()
        session.sessionPreset = .high
        session.usesApplicationAudioSession = false
        session.automaticallyConfiguresApplicationAudioSession = false
        // Removed: session.masterClock = hostClock

        guard let device = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .front)
        else { throw Err("No camera") }
        let input = try AVCaptureDeviceInput(device: device)
        guard session.canAddInput(input) else { throw Err("Cannot add camera input") }
        session.addInput(input)

        let q = DispatchQueue(label: "video.queue")
        videoOutput.setSampleBufferDelegate(self, queue: q)
        videoOutput.alwaysDiscardsLateVideoFrames = false
        guard session.canAddOutput(videoOutput) else { throw Err("Cannot add video output") }
        session.addOutput(videoOutput)
        if #available(iOS 17.0, *) {
            // Set video output rotation to 90 degrees for portrait orientation
            videoOutput.connection(with: .video)?.videoRotationAngle = 90
        } else {
            videoOutput.connection(with: .video)?.videoOrientation = .portrait
        }
        session.commitConfiguration()
    }

    private func setupWriter() throws {
        try? FileManager.default.removeItem(at: outputURL)
        writer = try AVAssetWriter(outputURL: outputURL, fileType: .mov)

        // Video
        let settings: [String: Any] = [
            AVVideoCodecKey: AVVideoCodecType.h264,
            AVVideoWidthKey: 1080,
            AVVideoHeightKey: 1920
        ]
        videoInput = AVAssetWriterInput(mediaType: .video, outputSettings: settings)
        videoInput.expectsMediaDataInRealTime = true
        // Video orientation is now matched by the preview layer for iOS 17+ and no input transform is necessary
        
        guard writer.canAdd(videoInput) else { throw Err("Cannot add video input") }
        writer.add(videoInput)

        writer.startWriting()
        writer.startSession(atSourceTime: CMClockGetTime(hostClock))
    }

    private func setupMotion() {
        guard hmm.isDeviceMotionAvailable else {
            onError?(Err("Headphone motion not available. Connect AirPods and try again."))
            return
        }
        // CMHeadphoneMotionManager does not expose deviceMotionUpdateInterval; sample rate is managed by the system (~100 Hz).
        motionQueue.qualityOfService = .userInteractive
        hmm.startDeviceMotionUpdates(to: motionQueue) { [weak self] m, _ in
            guard let s = self, let m = m else { return }
            s.ingest(m)
            s.deviceMotionHandler?(m)
        }
#if DEBUG
        print("IMU: started deviceMotion updates")
#endif
    }

    private func startBatchTimer() {
        let t = DispatchSource.makeTimerSource(queue: .global(qos: .userInitiated))
        t.schedule(deadline: .now() + .milliseconds(10), repeating: .milliseconds(10))
        t.setEventHandler { [weak self] in self?.flushBatch() }
        t.resume()
        batchTimer = t
    }

    // MARK: IMU ingest & flush
    private func ingest(_ m: CMDeviceMotion) {
        if batchStartSeconds == nil { batchStartSeconds = m.timestamp }
        let dt = m.timestamp - (batchStartSeconds ?? m.timestamp)
        let dtNs = UInt32(max(0, min(Double(UInt32.max)/1e9, dt)) * 1e9)
        events.append(MotionEvent(dtNs: dtNs,
                                  ax: Float(m.userAcceleration.x),
                                  ay: Float(m.userAcceleration.y),
                                  az: Float(m.userAcceleration.z),
                                  gx: Float(m.rotationRate.x),
                                  gy: Float(m.rotationRate.y),
                                  gz: Float(m.rotationRate.z),
                                  label: nil))
#if DEBUG
        debugIMUSampleCounter += 1
        if debugIMUSampleCounter % debugPrintIMUSamplesEvery == 0 {
            let ax = m.userAcceleration.x, ay = m.userAcceleration.y, az = m.userAcceleration.z
            let gx = m.rotationRate.x,    gy = m.rotationRate.y,    gz = m.rotationRate.z
            let t  = m.timestamp
            let dts = dt
            print(String(format: "[IMU] t=%.6f dt=%.6f ax=%.4f ay=%.4f az=%.4f gx=%.4f gy=%.4f gz=%.4f", t, dts, ax, ay, az, gx, gy, gz))
        }
#endif
    }

    private func flushBatch() {
        guard !events.isEmpty, let t0 = batchStartSeconds else { return }
        guard let csvFileHandle = csvFileHandle else { return }
        
        // Write CSV header if file is empty
        if let fileSize = try? csvFileHandle.seekToEnd(), fileSize == 0 {
            if let headerData = "timestamp,dtNs,ax,ay,az,gx,gy,gz\n".data(using: .utf8) {
                csvFileHandle.write(headerData)
            }
        }
        
        var csvLines = ""
        for event in events {
            // Calculate absolute timestamp in seconds
            let eventTimestampSeconds = t0 + Double(event.dtNs) / 1e9
            // Format timestamp as ISO8601 with fractional seconds or as seconds since reference
            // Here using seconds with 9 decimal places for simplicity
            let timestampString = String(format: "%.9f", eventTimestampSeconds)
            let line = "\(timestampString),\(event.dtNs),\(event.ax),\(event.ay),\(event.az),\(event.gx),\(event.gy),\(event.gz)\n"
            csvLines.append(line)
        }
        
#if DEBUG
        print("IMU batch written:", events.count, "samples")
#endif

        if let data = csvLines.data(using: .utf8) {
            csvFileHandle.write(data)
        }

        // Flush bytes to disk so external share targets don't read a partial packet
        if #available(iOS 13.0, *) {
            try? csvFileHandle.synchronize()
        } else {
            csvFileHandle.synchronizeFile()
        }

        events.removeAll(keepingCapacity: true)
        // Reset for the next batch window; next ingest will set a new t0
        batchStartSeconds = nil
    }

    // MARK: Video delegate
    func captureOutput(_ output: AVCaptureOutput, didOutput sb: CMSampleBuffer, from connection: AVCaptureConnection) {
        guard let writer = writer,
              let videoInput = videoInput,
              writer.status == .writing else { return }
        videoWritingQueue.async {
            if videoInput.isReadyForMoreMediaData {
                videoInput.append(sb)
            }
        }
    }

    /// Attempts to start device motion and calls the completion with true if a real sample is received within 1.5s.
    func trialDeviceMotionCheck(completion: @escaping (Bool) -> Void) {
        // Prevent motion check while recording
        if isRecording {
            completion(false)
            return
        }
        
        guard hmm.isDeviceMotionAvailable else {
            completion(false)
            return
        }
        var didReceiveMotion = false
        let checkQueue = OperationQueue()
        checkQueue.qualityOfService = .userInitiated
        hmm.startDeviceMotionUpdates(to: checkQueue) { m, _ in
            if m != nil && !didReceiveMotion {
                didReceiveMotion = true
                self.hmm.stopDeviceMotionUpdates()
                completion(true)
                self.deviceMotionHandler?(m)
            }
        }
        // Timeout after 1.5 seconds
        DispatchQueue.global().asyncAfter(deadline: .now() + 1.5) {
            if !didReceiveMotion {
                self.hmm.stopDeviceMotionUpdates()
                completion(false)
                self.deviceMotionHandler?(nil)
            }
        }
    }
    
    private func postprocessCSVIfNeeded() {
        // Only apply when the initial selection was Not Eating (false)
        guard let csvURL = self.csvURL, recordingLabel == false else { return }
        do {
            let data = try Data(contentsOf: csvURL)
            guard let text = String(data: data, encoding: .utf8) else { return }
            // Split into lines preserving order
            var lines = text.split(separator: "\n", omittingEmptySubsequences: false).map(String.init)
            guard !lines.isEmpty else { return }
            // If header already contains label, do nothing
            if lines[0].contains(",label") { return }
            // Append label column to header
            lines[0] += ",label"
            // Append ",false" to each non-empty data line
            for i in 1..<lines.count {
                if !lines[i].isEmpty { lines[i] += ",false" }
            }
            let newText = lines.joined(separator: "\n")
            // Write atomically via a temp file
            let tmpURL = csvURL.deletingLastPathComponent().appendingPathComponent(csvURL.lastPathComponent + ".tmp")
            try newText.data(using: .utf8)?.write(to: tmpURL, options: .atomic)
            // Replace original
            try FileManager.default.replaceItemAt(csvURL, withItemAt: tmpURL)
        } catch {
            // Non-fatal; surface via onError if provided
            onError?(error)
        }
    }
}

