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
        print("Camera Manager: Start Recording")
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
        guard movieOutput.isRecording else {
            throw CameraError.setupFailed // Handle cases where stopRecording is called when no recording is active
        }
        
        return try await withCheckedThrowingContinuation { continuation in
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
        DispatchQueue.main.async {
            self.videoURL = outputFileURL
        }
        print("Movie recorded to: \(outputFileURL)")
    }

}
