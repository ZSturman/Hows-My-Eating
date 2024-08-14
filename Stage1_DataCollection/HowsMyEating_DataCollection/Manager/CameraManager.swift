//
//  CameraManager.swift
//  HowsMyEating_DataCollection
//
//  Created by Zachary Sturman on 8/14/24.
//

import Foundation
import SwiftUI
import AVFoundation

class CameraManager: NSObject, ObservableObject, AVCaptureFileOutputRecordingDelegate {
    
    let output = AVCaptureMovieFileOutput()
    // An internal alias for the output.
    private var movieOutput: AVCaptureMovieFileOutput { output }
    private var delegate: MovieCaptureDelegate?
    
    private let session = AVCaptureSession()
    private var previewLayer: AVCaptureVideoPreviewLayer?
    
    @Published var isRecording = false
    @Published var videoURL: URL?

    // MARK: - Setup Camera
    func setupCamera() {
        session.beginConfiguration()
        
        // Setup camera input
        guard let videoDevice = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .front) else {
            print("Default video device not available.")
            return
        }
        
        do {
            let videoInput = try AVCaptureDeviceInput(device: videoDevice)
            if session.canAddInput(videoInput) {
                session.addInput(videoInput)
            }
        } catch {
            print("Unable to add video input: \(error)")
            return
        }
        
        // Setup microphone input
        guard let audioDevice = AVCaptureDevice.default(for: .audio) else {
            print("Default audio device not available.")
            return
        }
        
        do {
            let audioInput = try AVCaptureDeviceInput(device: audioDevice)
            if session.canAddInput(audioInput) {
                session.addInput(audioInput)
            }
        } catch {
            print("Unable to add audio input: \(error)")
            return
        }
        
        // Setup movie output
        if session.canAddOutput(movieOutput) {
            session.addOutput(movieOutput)
        }
        
        session.commitConfiguration()
        
        // Setup preview layer
        previewLayer = AVCaptureVideoPreviewLayer(session: session)
        previewLayer?.videoGravity = .resizeAspectFill
    }
    
    // MARK: - Start Camera Preview
    func startPreview(in view: UIView) {
        guard let previewLayer = previewLayer else { return }
        previewLayer.frame = view.bounds
        view.layer.addSublayer(previewLayer)
        
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            self?.session.startRunning()
        }
    }
    
    // MARK: - Start Recording
    func startRecording() {
        // Return early if already recording.
        guard !movieOutput.isRecording else { return }
        
        guard let connection = movieOutput.connection(with: .video) else {
            fatalError("Configuration error. No video connection found.")
        }

        // Configure connection for HEVC capture.
        if movieOutput.availableVideoCodecTypes.contains(.hevc) {
            movieOutput.setOutputSettings([AVVideoCodecKey: AVVideoCodecType.hevc], for: connection)
        }

        // Enable video stabilization if the connection supports it.
        if connection.isVideoStabilizationSupported {
            connection.preferredVideoStabilizationMode = .auto
        }
        
        delegate = MovieCaptureDelegate()
        movieOutput.startRecording(to: URL.applicationSupportDirectory.appendingPathComponent("\(Date().timeIntervalSince1970).mov"), recordingDelegate: delegate!)
    }
    
    
    func stopRecording() async throws -> Movie {
        // Use a continuation to adapt the delegate-based capture API to an async interface.
        return try await withCheckedThrowingContinuation { continuation in
            // Set the continuation on the delegate to handle the capture result.
            delegate?.continuation = continuation
            movieOutput.stopRecording()
        }
    }
    
    // MARK: - Movie capture delegate
    /// A delegate object that responds to the capture output finalizing movie recording.
    private class MovieCaptureDelegate: NSObject, AVCaptureFileOutputRecordingDelegate {
        
        var continuation: CheckedContinuation<Movie, Error>?
        
        func fileOutput(_ output: AVCaptureFileOutput, didFinishRecordingTo outputFileURL: URL, from connections: [AVCaptureConnection], error: Error?) {
            if let error {
                // If an error occurs, throw it to the caller.
                continuation?.resume(throwing: error)
            } else {
                // Return a new movie object.
                continuation?.resume(returning: Movie(url: outputFileURL))
            }
        }
    }

    // MARK: - AVCaptureFileOutputRecordingDelegate
    func fileOutput(_ output: AVCaptureFileOutput, didFinishRecordingTo outputFileURL: URL, from connections: [AVCaptureConnection], error: Error?) {
        if let error = error {
            print("Error recording movie: \(error)")
            return
        }
        videoURL = outputFileURL
        print("Movie recorded to: \(outputFileURL)")
    }
}






//
///// An object that manages a movie capture output to record videos.
//final class MovieCapture: OutputService {
//
//    /// A value that indicates the current state of movie capture.
//    @Published private(set) var captureActivity: CaptureActivity = .idle
//
//
//    // The interval at which to update the recording time.
//
//
//    // A Boolean value that indicates whether the currently selected camera's
//    // active format supports HDR.
//    private var isHDRSupported = false
//
//    // MARK: - Capturing a movie
//
//    /// Starts movie recording.
//    func startRecording() {
//        // Return early if already recording.
//        guard !movieOutput.isRecording else { return }
//
//        guard let connection = movieOutput.connection(with: .video) else {
//            fatalError("Configuration error. No video connection found.")
//        }
//
//        // Configure connection for HEVC capture.
//        if movieOutput.availableVideoCodecTypes.contains(.hevc) {
//            movieOutput.setOutputSettings([AVVideoCodecKey: AVVideoCodecType.hevc], for: connection)
//        }
//
//        // Enable video stabilization if the connection supports it.
//        if connection.isVideoStabilizationSupported {
//            connection.preferredVideoStabilizationMode = .auto
//        }
//
//        // Start a timer to update the recording time.
//        startMonitoringDuration()
//
//        delegate = MovieCaptureDelegate()
//        movieOutput.startRecording(to: URL.movieFileURL, recordingDelegate: delegate!)
//    }
//
//    /// Stops movie recording.
//    /// - Returns: A `Movie` object that represents the captured movie.
//    func stopRecording() async throws -> Movie {
//        // Use a continuation to adapt the delegate-based capture API to an async interface.
//        return try await withCheckedThrowingContinuation { continuation in
//            // Set the continuation on the delegate to handle the capture result.
//            delegate?.continuation = continuation
//
//            /// Stops recording, which causes the output to call the `MovieCaptureDelegate` object.
//            movieOutput.stopRecording()
//            stopMonitoringDuration()
//        }
//    }
//
//    // MARK: - Movie capture delegate
//    /// A delegate object that responds to the capture output finalizing movie recording.
//    private class MovieCaptureDelegate: NSObject, AVCaptureFileOutputRecordingDelegate {
//
//        var continuation: CheckedContinuation<Movie, Error>?
//
//        func fileOutput(_ output: AVCaptureFileOutput, didFinishRecordingTo outputFileURL: URL, from connections: [AVCaptureConnection], error: Error?) {
//            if let error {
//                // If an error occurs, throw it to the caller.
//                continuation?.resume(throwing: error)
//            } else {
//                // Return a new movie object.
//                continuation?.resume(returning: Movie(url: outputFileURL))
//            }
//        }
//    }
//
//    // MARK: - Monitoring recorded duration
//
//    // Starts a timer to update the recording time.
//    private func startMonitoringDuration() {
//        captureActivity = .movieCapture()
//        timerCancellable = Timer.publish(every: refreshInterval, on: .main, in: .common)
//            .autoconnect()
//            .sink { [weak self] _ in
//                guard let self else { return }
//                // Poll the movie output for its recorded duration.
//                let duration = movieOutput.recordedDuration.seconds
//                captureActivity = .movieCapture(duration: duration)
//            }
//    }
//
//    /// Stops the timer and resets the time to `CMTime.zero`.
//    private func stopMonitoringDuration() {
//        timerCancellable?.cancel()
//        captureActivity = .idle
//    }
//
//    func updateConfiguration(for device: AVCaptureDevice) {
//        // The app supports HDR video capture if the active format supports it.
//        isHDRSupported = device.activeFormat10BitVariant != nil
//    }
//
//    // MARK: - Configuration
//    /// Returns the capabilities for this capture service.
//    var capabilities: CaptureCapabilities {
//        CaptureCapabilities(isHDRSupported: isHDRSupported)
//    }
//}




/// An actor that manages the capture pipeline, which includes the capture session, device inputs, and capture outputs.
/// The app defines it as an `actor` type to ensure that all camera operations happen off of the `@MainActor`.
//actor CaptureService {
//
//    @Published private(set) var captureActivity: CaptureActivity = .idle
//    @Published private(set) var captureCapabilities = CaptureCapabilities.unknown
//    @Published private(set) var isInterrupted = false
//    @Published var isHDRVideoEnabled = false
//
//
//
//    private let movieCapture = MovieCapture()
//    private var outputServices: [any OutputService] { [ movieCapture] }
//    private var activeVideoInput: AVCaptureDeviceInput?
//    private(set) var captureMode = CaptureMode.video
//    private let deviceLookup = DeviceLookup()
//    private let systemPreferredCamera = SystemPreferredCameraObserver()
//
//    // An object that monitors video device rotations.
//    private var rotationCoordinator: AVCaptureDevice.RotationCoordinator!
//    private var rotationObservers = [AnyObject]()
//    private var isSetUp = false
//
//    init() {
//        logger.debug("Creating default preview source.")
//        previewSource = DefaultPreviewSource(session: captureSession)
//    }
    
    // MARK: - Authorization
//    var isAuthorized: Bool {
//        get async {
//            let status = AVCaptureDevice.authorizationStatus(for: .video)
//            // Determine whether a person previously authorized camera access.
//            var isAuthorized = status == .authorized
//            // If the system hasn't determined their authorization status,
//            // explicitly prompt them for approval.
//            if status == .notDetermined {
//                isAuthorized = await AVCaptureDevice.requestAccess(for: .video)
//            }
//            return isAuthorized
//        }
//    }
    
//    // MARK: - Capture session life cycle
//    func start() async throws {
//        // Exit early if not authorized or the session is already running.
//        guard await isAuthorized, !captureSession.isRunning else { return }
//        // Configure the session and start it.
//        try setUpSession()
//        captureSession.startRunning()
//    }
    
//    // MARK: - Capture setup
//    private func setUpSession() throws {
//        logger.debug("Setting up capture session.")
//        guard !isSetUp else { return }
//
//        observeNotifications()
//
//        do {
//            let defaultCamera = try deviceLookup.defaultCamera
//            let defaultMic = try deviceLookup.defaultMic
//
//            logger.debug("Adding video input for the default camera.")
//            activeVideoInput = try addInput(for: defaultCamera)
//            logger.debug("Adding audio input for the default microphone.")
//            try addInput(for: defaultMic)
//
//            // Rest of the setup code...
//        } catch {
//            logger.error("Failed to set up the capture session: \(error.localizedDescription)")
//            throw CameraError.setupFailed
//        }
//    }

//    // Adds an input to the capture session to connect the specified capture device.
//    @discardableResult
//    private func addInput(for device: AVCaptureDevice) throws -> AVCaptureDeviceInput {
//        let input = try AVCaptureDeviceInput(device: device)
//        if captureSession.canAddInput(input) {
//            captureSession.addInput(input)
//        } else {
//            throw CameraError.addInputFailed
//        }
//        return input
//    }
    
//    // Adds an output to the capture session to connect the specified capture device, if allowed.
//    private func addOutput(_ output: AVCaptureOutput) throws {
//        if captureSession.canAddOutput(output) {
//            captureSession.addOutput(output)
//        } else {
//            throw CameraError.addOutputFailed
//        }
////    }
//
//    // The device for the active video input.
//    private var currentDevice: AVCaptureDevice {
//        guard let device = activeVideoInput?.device else {
//            fatalError("No device found for current video input.")
//        }
//        return device
//    }
//
    // MARK: - Capture mode selection
    
    /// Changes the mode of capture, which can be `photo` or `video`.
    ///
    /// - Parameter `captureMode`: The capture mode to enable.
//    func setCaptureMode(_ captureMode: CaptureMode) throws {
//        // Update the internal capture mode value before performing the session configuration.
//        self.captureMode = captureMode
//
//        // Change the configuration atomically.
//        captureSession.beginConfiguration()
//        defer { captureSession.commitConfiguration() }
//
//        // Ensure the active input is added to the session before output
//        guard activeVideoInput != nil else {
//            throw CameraError.setupFailed
//        }
//
//        // Check if session can add movie output
//        if captureMode == .video {
//            captureSession.sessionPreset = .high
//            try addOutput(movieCapture.output)
//            if isHDRVideoEnabled {
//                setHDRVideoEnabled(true)
//            }
//        }
//
//        // Update the advertised capabilities after reconfiguration.
//        updateCaptureCapabilities()
//    }
    
//    // MARK: - Device selection
//    func selectNextVideoDevice() {
//        // The array of available video capture devices.
//        let videoDevices = deviceLookup.cameras
//
//        // Find the index of the currently selected video device.
//        let selectedIndex = videoDevices.firstIndex(of: currentDevice) ?? 0
//        // Get the next index.
//        var nextIndex = selectedIndex + 1
//        // Wrap around if the next index is invalid.
//        if nextIndex == videoDevices.endIndex {
//            nextIndex = 0
//        }
//
//        let nextDevice = videoDevices[nextIndex]
//        // Change the session's active capture device.
//        changeCaptureDevice(to: nextDevice)
//
//        // The app only calls this method in response to the user requesting to switch cameras.
//        // Set the new selection as the user's preferred camera.
//        AVCaptureDevice.userPreferredCamera = nextDevice
//    }
//
    // Changes the device the service uses for video capture.
//    private func changeCaptureDevice(to device: AVCaptureDevice) {
//        // The service must have a valid video input prior to calling this method.
//        guard let currentInput = activeVideoInput else { fatalError() }
//
//        // Bracket the following configuration in a begin/commit configuration pair.
//        captureSession.beginConfiguration()
//        defer { captureSession.commitConfiguration() }
//
//        // Remove the existing video input before attempting to connect a new one.
//        captureSession.removeInput(currentInput)
//        do {
//            // Attempt to connect a new input and device to the capture session.
//            activeVideoInput = try addInput(for: device)
//            // Configure a new rotation coordinator for the new device.
//            createRotationCoordinator(for: device)
//            // Register for device observations.
//            observeSubjectAreaChanges(of: device)
//            // Update the service's advertised capabilities.
//            updateCaptureCapabilities()
//        } catch {
//            // Reconnect the existing camera on failure.
//            captureSession.addInput(currentInput)
//        }
//    }
    
//    private func monitorSystemPreferredCamera() {
//        Task {
//            for await camera in systemPreferredCamera.changes {
//                // If the SPC isn't the currently selected camera, attempt to change to that device.
//                if let camera, currentDevice != camera {
//                    logger.debug("Switching camera selection to the system-preferred camera.")
//                    changeCaptureDevice(to: camera)
//                }
//            }
//        }
//    }
    
    // MARK: - Rotation handling
    
//    /// Create a new rotation coordinator for the specified device and observe its state to monitor rotation changes.
//    private func createRotationCoordinator(for device: AVCaptureDevice) {
//        // Create a new rotation coordinator for this device.
//        rotationCoordinator = AVCaptureDevice.RotationCoordinator(device: device, previewLayer: videoPreviewLayer)
//
//        // Set initial rotation state on the preview and output connections.
//        updatePreviewRotation(rotationCoordinator.videoRotationAngleForHorizonLevelPreview)
//        updateCaptureRotation(rotationCoordinator.videoRotationAngleForHorizonLevelCapture)
//
//        // Cancel previous observations.
//        rotationObservers.removeAll()
//
//        // Add observers to monitor future changes.
//        rotationObservers.append(
//            rotationCoordinator.observe(\.videoRotationAngleForHorizonLevelPreview, options: .new) { [weak self] _, change in
//                guard let self, let angle = change.newValue else { return }
//                // Update the capture preview rotation.
//                Task { await self.updatePreviewRotation(angle) }
//            }
//        )
//
//        rotationObservers.append(
//            rotationCoordinator.observe(\.videoRotationAngleForHorizonLevelCapture, options: .new) { [weak self] _, change in
//                guard let self, let angle = change.newValue else { return }
//                // Update the capture preview rotation.
//                Task { await self.updateCaptureRotation(angle) }
//            }
//        )
//    }
    
//    private func updatePreviewRotation(_ angle: CGFloat) {
//        let previewLayer = videoPreviewLayer
//        Task { @MainActor in
//            // Set initial rotation angle on the video preview.
//            previewLayer.connection?.videoRotationAngle = angle
//        }
//    }
//
//    private func updateCaptureRotation(_ angle: CGFloat) {
//        // Update the orientation for all output services.
//        outputServices.forEach { $0.setVideoRotationAngle(angle) }
//    }
//
//    private var videoPreviewLayer: AVCaptureVideoPreviewLayer {
//        // Access the capture session's connected preview layer.
//        guard let previewLayer = captureSession.connections.compactMap({ $0.videoPreviewLayer }).first else {
//            fatalError("The app is misconfigured. The capture session should have a connection to a preview layer.")
//        }
//        return previewLayer
//    }
//
    // MARK: - Automatic focus and exposure
    
    /// Performs a one-time automatic focus and expose operation.
    ///
    /// The app calls this method as the result of a person tapping on the preview area.
//    func focusAndExpose(at point: CGPoint) {
//        // The point this call receives is in view-space coordinates. Convert this point to device coordinates.
//        let devicePoint = videoPreviewLayer.captureDevicePointConverted(fromLayerPoint: point)
//        do {
//            // Perform a user-initiated focus and expose.
//            try focusAndExpose(at: devicePoint, isUserInitiated: true)
//        } catch {
//            logger.debug("Unable to perform focus and exposure operation. \(error)")
//        }
//    }
//
//    // Observe notifications of type `subjectAreaDidChangeNotification` for the specified device.
//    private func observeSubjectAreaChanges(of device: AVCaptureDevice) {
//        // Cancel the previous observation task.
//        subjectAreaChangeTask?.cancel()
//        subjectAreaChangeTask = Task {
//            // Signal true when this notification occurs.
//            for await _ in NotificationCenter.default.notifications(named: AVCaptureDevice.subjectAreaDidChangeNotification, object: device).compactMap({ _ in true }) {
//                // Perform a system-initiated focus and expose.
//                try? focusAndExpose(at: CGPoint(x: 0.5, y: 0.5), isUserInitiated: false)
//            }
//        }
//    }
//    private var subjectAreaChangeTask: Task<Void, Never>?
    
//    private func focusAndExpose(at devicePoint: CGPoint, isUserInitiated: Bool) throws {
//        // Configure the current device.
//        let device = currentDevice
//
//        // The following mode and point of interest configuration requires obtaining an exclusive lock on the device.
//        try device.lockForConfiguration()
//
//        let focusMode = isUserInitiated ? AVCaptureDevice.FocusMode.autoFocus : .continuousAutoFocus
//        if device.isFocusPointOfInterestSupported && device.isFocusModeSupported(focusMode) {
//            device.focusPointOfInterest = devicePoint
//            device.focusMode = focusMode
//        }
//
//        let exposureMode = isUserInitiated ? AVCaptureDevice.ExposureMode.autoExpose : .continuousAutoExposure
//        if device.isExposurePointOfInterestSupported && device.isExposureModeSupported(exposureMode) {
//            device.exposurePointOfInterest = devicePoint
//            device.exposureMode = exposureMode
//        }
//        // Enable subject-area change monitoring when performing a user-initiated automatic focus and exposure operation.
//        // If this method enables change monitoring, when the device's subject area changes, the app calls this method a
//        // second time and resets the device to continuous automatic focus and exposure.
//        device.isSubjectAreaChangeMonitoringEnabled = isUserInitiated
//
//        // Release the lock.
//        device.unlockForConfiguration()
//    }
//
//    func checkrecordingStuff() throws {
//        print("Checking recording stuff PRINT")
//        logger.debug("Checking recording stuff DEBUG")
//        do {
//            let defaultCamera = try deviceLookup.defaultCamera
//            activeVideoInput = try addInput(for: defaultCamera)
//        } catch {
//            throw CameraError.setupFailed
//        }
//    }
    
//    // MARK: - Movie capture
//    func startRecording() {
//        do {
//            try checkrecordingStuff()
//            logger.debug("Starting movie capture.")
//            movieCapture.startRecording()
//        } catch {
//            logger.error("Failed to start recording due to setup error: \(error.localizedDescription)")
//            // Handle error accordingly
//            return
//        }
//    }
    
//    /// Stops the recording and returns the captured movie.
//    func stopRecording() async throws -> Movie {
//        logger.debug("Stopping movie capture.")
//        return try await movieCapture.stopRecording()
//
//    }
//
//    /// Sets whether the app captures HDR video.
//    func setHDRVideoEnabled(_ isEnabled: Bool) {
//        // Bracket the following configuration in a begin/commit configuration pair.
//        captureSession.beginConfiguration()
//        defer { captureSession.commitConfiguration() }
//        do {
//            // If the current device provides a 10-bit HDR format, enable it for use.
//            if isEnabled, let format = currentDevice.activeFormat10BitVariant {
//                try currentDevice.lockForConfiguration()
//                currentDevice.activeFormat = format
//                currentDevice.unlockForConfiguration()
//                isHDRVideoEnabled = true
//            } else {
//                captureSession.sessionPreset = .high
//                isHDRVideoEnabled = false
//            }
//        } catch {
//            logger.error("Unable to obtain lock on device and can't enable HDR video capture.")
//        }
//    }
    
    // MARK: - Internal state management
    /// Updates the state of the actor to ensure its advertised capabilities are accurate.
    ///
    /// When the capture session changes, such as changing modes or input devices, the service
    /// calls this method to update its configuration and capabilities. The app uses this state to
    /// determine which features to enable in the user interface.
//    private func updateCaptureCapabilities() {
//        // Update the output service configuration.
//        outputServices.forEach { $0.updateConfiguration(for: currentDevice) }
//
//            captureCapabilities = movieCapture.capabilities
//
//    }
//

    
    /// Observe capture-related notifications.
//    private func observeNotifications() {
//        Task {
//            for await reason in NotificationCenter.default.notifications(named: AVCaptureSession.wasInterruptedNotification)
//                .compactMap({ $0.userInfo?[AVCaptureSessionInterruptionReasonKey] as AnyObject? })
//                .compactMap({ AVCaptureSession.InterruptionReason(rawValue: $0.integerValue) }) {
//                /// Set the `isInterrupted` state as appropriate.
//                isInterrupted = [.audioDeviceInUseByAnotherClient, .videoDeviceInUseByAnotherClient].contains(reason)
//            }
//        }
//
//        Task {
//            // Await notification of the end of an interruption.
//            for await _ in NotificationCenter.default.notifications(named: AVCaptureSession.interruptionEndedNotification) {
//                isInterrupted = false
//            }
//        }
//
//        Task {
//            for await error in NotificationCenter.default.notifications(named: AVCaptureSession.runtimeErrorNotification)
//                .compactMap({ $0.userInfo?[AVCaptureSessionErrorKey] as? AVError }) {
//                // If the system resets media services, the capture session stops running.
//                if error.code == .mediaServicesWereReset {
//                    if !captureSession.isRunning {
//                        captureSession.startRunning()
//                    }
//                }
//            }
//        }
//    }
//}





//
//    // MARK: - Properties
//
//    private(set) var status: CameraStatus = .unknown
//
//    private(set) var captureActivity: CaptureActivity = .idle
//
//    var previewSource: PreviewSource {
//        return captureService.previewSource
//    }
//
//
//    private(set) var isSwitchingModes: Bool = false
//
//    private(set) var isSwitchingVideoDevices: Bool = false
//
//    var shouldFlashScreen: Bool = false
//
//    private(set) var isHDRVideoSupported: Bool = false
//
//    var isHDRVideoEnabled: Bool = false {
//        didSet {
//            Task {
//                await captureService.setHDRVideoEnabled(isHDRVideoEnabled)
//            }
//        }
//    }
//
//    private(set) var thumbnail: CGImage?
//
//    private(set) var error: Error?
//
//    private let mediaLibrary = MediaLibrary()
//
//    private let captureService = CaptureService()
//
//    // MARK: - Methods
//    init() { }
//
//    func start() async {
//        logger.debug("Starting camera.")
//        guard await captureService.isAuthorized else {
//            status = .unauthorized
//            return
//        }
//        do {
//            try await captureService.start()
//            observeState()
//            status = .running
//        } catch {
//            logger.error("Failed to start capture service: \(error.localizedDescription)")
//            status = .failed
//
//        }
//    }
//
//    func switchVideoDevices() async {
//        isSwitchingVideoDevices = true
//        defer { isSwitchingVideoDevices = false }
//        await captureService.selectNextVideoDevice()
//    }
//
//    func focusAndExpose(at point: CGPoint) async {
//        await captureService.focusAndExpose(at: point)
//    }
//
//
//    func toggleRecording() async -> Movie? {
//        logger.debug("Toggling recording")
//        switch await captureService.captureActivity {
//        case .movieCapture:
//            do {
//                let movie = try await captureService.stopRecording()
//                try await mediaLibrary.save(movie: movie)
//                return movie
//            } catch {
//                self.error = error
//                logger.error("Failed to stop recording: \(error.localizedDescription)")
//                return nil
//            }
//        default:
//            await captureService.startRecording()
//            return nil
//        }
//    }
//
//    private func flashScreen() {
//        shouldFlashScreen = true
//        withAnimation(.linear(duration: 0.01)) {
//            shouldFlashScreen = false
//        }
//    }
//
//    private func observeState() {
//        Task {
//            for await thumbnail in mediaLibrary.thumbnails.compactMap({ $0 }) {
//                self.thumbnail = thumbnail
//            }
//        }
//
//        Task {
//            for await activity in await captureService.$captureActivity.values {
//                if activity.willCapture {
//                    flashScreen()
//                } else {
//                    captureActivity = activity
//                }
//            }
//        }
//
//        Task {
//            for await capabilities in await captureService.$captureCapabilities.values {
//                isHDRVideoSupported = capabilities.isHDRSupported
//            }
//        }
//    }
//}
