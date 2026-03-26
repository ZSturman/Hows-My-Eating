//
//  MotionManager.swift
//  HowsMyEating
//
//  Created by Zachary Sturman on 2/7/25.
//

import Foundation
import CoreMotion
import SwiftUI
import SceneKit
import simd
import CoreML

final class MotionManager: NSObject, ObservableObject, CMHeadphoneMotionManagerDelegate {
    private var manager: CMHeadphoneMotionManager = CMHeadphoneMotionManager()

    @Published var connectionStatus: Bool = false
    @Published var motionDataAvailable: Bool = false
    @Published var isMotionDataUnavailable: Bool = false
    // Published property to hold the live prediction output ("chew" or "not-chew")
    @Published var chewingPrediction: String = "unknown"

    private(set) var motionDataArray: [MotionData] = []
    private var referenceFrame = matrix_identity_float4x4
    private var referenceFrameHasChanged: Bool = false

    var onMotionUpdate: ((float4x4, float4x4) -> Void)?
    // Buffers to accumulate 100 samples of sensor data.
    private var rotationRateXBuffer: [Double] = []
    private var rotationRateYBuffer: [Double] = []
    private var rotationRateZBuffer: [Double] = []
    private var timestampBuffer: [Double] = []
    
    @Published var liveRotationRate: RotationRate = RotationRate(x: 0, y: 0, z: 0)
    @Published var liveUserAcceleration: UserAcceleration = UserAcceleration(x: 0, y: 0, z: 0)
    @Published var liveAttitude: Attitude = Attitude(roll: 0, pitch: 0, yaw: 0)

    // Buffer for the LSTM state (400 elements). It is initially nil and set to zeros.
    private var lstmState: MLMultiArray?

    // MARK: - Updated Prediction Method

    private func performChewingPrediction(for motion: CMDeviceMotion) {
        rotationRateXBuffer.append(motion.rotationRate.x)
        rotationRateYBuffer.append(motion.rotationRate.y)
        rotationRateZBuffer.append(motion.rotationRate.z)
        timestampBuffer.append(motion.timestamp)
        
        let windowSize = 100
        guard rotationRateXBuffer.count >= windowSize else { return }
        
        do {
            // Log input data
            print("Rotation Rate X: \(rotationRateXBuffer.prefix(windowSize))")
            print("Rotation Rate Y: \(rotationRateYBuffer.prefix(windowSize))")
            print("Rotation Rate Z: \(rotationRateZBuffer.prefix(windowSize))")
            print("Timestamps: \(timestampBuffer.prefix(windowSize))")
            
            let rotationRateXArray = try MLMultiArray(shape: [NSNumber(value: windowSize)], dataType: .double)
            let rotationRateYArray = try MLMultiArray(shape: [NSNumber(value: windowSize)], dataType: .double)
            let rotationRateZArray = try MLMultiArray(shape: [NSNumber(value: windowSize)], dataType: .double)
            let timestampArray     = try MLMultiArray(shape: [NSNumber(value: windowSize)], dataType: .double)

            for i in 0..<windowSize {
                rotationRateXArray[i] = NSNumber(value: rotationRateXBuffer[i])
                rotationRateYArray[i] = NSNumber(value: rotationRateYBuffer[i])
                rotationRateZArray[i] = NSNumber(value: rotationRateZBuffer[i])
                timestampArray[i]     = NSNumber(value: timestampBuffer[i])
            }
            
            if lstmState == nil {
                lstmState = try MLMultiArray(shape: [NSNumber(value: 400)], dataType: .double)
                for i in 0..<400 {
                    lstmState![i] = 0.0
                }
            }

            // Log LSTM state
            print("LSTM State: \(lstmState!)")

            let input = HowsMyEating_V1Input(
                rotationRateX: rotationRateXArray,
                rotationRateY: rotationRateYArray,
                rotationRateZ: rotationRateZArray,
                timestamp: timestampArray,
                stateIn: lstmState!
            )

            // Perform the prediction
            let prediction = try chewingClassifier.prediction(input: input)

            // Log prediction output
            print("Prediction Label: \(prediction.label)")
            print("Prediction State Out: \(prediction.stateOut)")
            
            lstmState = prediction.stateOut

            DispatchQueue.main.async {
                self.chewingPrediction = prediction.label
            }

            rotationRateXBuffer.removeFirst()
            rotationRateYBuffer.removeFirst()
            rotationRateZBuffer.removeFirst()
            timestampBuffer.removeFirst()

        } catch {
            print("ML Prediction error: \(error)")
        }
    }


    // Lazy-load the Core ML model.
    private lazy var chewingClassifier: HowsMyEating_V1 = {
        do {
            let config = MLModelConfiguration()
            return try HowsMyEating_V1(configuration: config)
        } catch {
            fatalError("Failed to load Core ML model: \(error)")
        }
    }()

    override init() {
        super.init()
        manager.delegate = self
        initializeMotionTracking()
    }

    private func initializeMotionTracking() {
        self.motionDataAvailable = manager.isDeviceMotionAvailable
        print("Motion data availability: \(self.motionDataAvailable)")
        
        if motionDataAvailable {
            startMotionTracking()
        } else {
            print("Device motion is not available.")
            self.isMotionDataUnavailable = true
        }
    }

    private func startMotionTracking() {
        guard manager.isDeviceMotionAvailable else {
            print("Device motion updates not started")
            return
        }
        
        manager.startDeviceMotionUpdates(to: OperationQueue.main) { [weak self] (deviceMotion, error) in
            guard let self = self else { return }
            
            if let motion = deviceMotion {
                self.collectMotionData(from: motion)
            } else if let error = error {
                self.headphoneMotionManager(self.manager, didFail: error)
            }
        }
        print("Started device motion updates")
    }

    func setReferenceFrame() {
        guard let deviceMotion = manager.deviceMotion else { return }
        referenceFrame = float4x4(rotationMatrix: deviceMotion.attitude.rotationMatrix).inverse
        referenceFrameHasChanged = true
    }

    private func collectMotionData(from motion: CMDeviceMotion) {
        let rotation = float4x4(rotationMatrix: motion.attitude.rotationMatrix)
        
        DispatchQueue.main.async {
            self.liveRotationRate = RotationRate(x: motion.rotationRate.x, y: motion.rotationRate.y, z: motion.rotationRate.z)
            self.liveUserAcceleration = UserAcceleration(x: motion.userAcceleration.x, y: motion.userAcceleration.y, z: motion.userAcceleration.z)
            self.liveAttitude = Attitude(roll: motion.attitude.roll, pitch: motion.attitude.pitch, yaw: motion.attitude.yaw)
        }

        // Apply transformation only if the reference frame has changed
        let transformedRotation: TransformedRotation = {
            if referenceFrameHasChanged {
                let mirrorTransform = simd_float4x4([
                    simd_float4(-1.0, 0.0, 0.0, 0.0),
                    simd_float4( 0.0, 1.0, 0.0, 0.0),
                    simd_float4( 0.0, 0.0, 1.0, 0.0),
                    simd_float4( 0.0, 0.0, 0.0, 1.0)
                ])
                let transformedMatrix = mirrorTransform * rotation * referenceFrame
                referenceFrameHasChanged = false
                return TransformedRotation(
                    x: Double(transformedMatrix.columns.0.x),
                    y: Double(transformedMatrix.columns.0.y),
                    z: Double(transformedMatrix.columns.0.z),
                    w: Double(transformedMatrix.columns.3.w)
                )
            } else {
                return TransformedRotation.zero
            }
        }()

        // Pass the live rotation data to any update handler
        onMotionUpdate?(rotation, referenceFrame)
        
        // --- Begin Core ML Prediction Integration ---
        performChewingPrediction(for: motion)
        // --- End Core ML Prediction Integration ---

        let motionElement = MotionData(
            timestamp: Date().timeIntervalSince1970,
            attitude: Attitude(roll: motion.attitude.roll, pitch: motion.attitude.pitch, yaw: motion.attitude.yaw),
            rotationRate: RotationRate(x: motion.rotationRate.x, y: motion.rotationRate.y, z: motion.rotationRate.z),
            userAcceleration: UserAcceleration(x: motion.userAcceleration.x, y: motion.userAcceleration.y, z: motion.userAcceleration.z),
            gravity: Gravity(x: motion.gravity.x, y: motion.gravity.y, z: motion.gravity.z),
            transformedRotation: transformedRotation
        )

        DispatchQueue.main.async {
            self.motionDataArray.append(motionElement)
            self.isMotionDataUnavailable = false
        }
    }


    func startRecording() {
        reset()
        guard motionDataAvailable else {
            print("Motion data unavailable. Recording not started.")
            self.isMotionDataUnavailable = true
            return
        }

        print("Device motion is available. Starting recording.")
        manager.startDeviceMotionUpdates(to: OperationQueue.main) { [weak self] (deviceMotion, error) in
            guard let self = self else { return }

            if let motion = deviceMotion {
                self.collectMotionData(from: motion)
            } else if let error = error {
                self.headphoneMotionManager(self.manager, didFail: error)
            }
        }
    }

    func stopRecording() async throws -> [MotionData] {
        manager.stopDeviceMotionUpdates()
        print("Final motion data count: \(motionDataArray.count)")
        return motionDataArray
    }

    func reset() {
        setReferenceFrame()
        motionDataArray = []
        isMotionDataUnavailable = false
    }

    // MARK: - CMHeadphoneMotionManagerDelegate
    
    func headphoneMotionManagerDidConnect(_ manager: CMHeadphoneMotionManager) {
        DispatchQueue.main.async {
            self.connectionStatus = true
            print("Headphones connected")
        }
    }
    
    func headphoneMotionManagerDidDisconnect(_ manager: CMHeadphoneMotionManager) {
        DispatchQueue.main.async {
            self.connectionStatus = false
            print("Headphones disconnected")
        }
    }

    func headphoneMotionManager(_ motionManager: CMHeadphoneMotionManager, didUpdate deviceMotion: CMDeviceMotion) {
        collectMotionData(from: deviceMotion)
    }
    
    func headphoneMotionManager(_ motionManager: CMHeadphoneMotionManager, didFail error: Error) {
        print("Motion update failed with error: \(error)")
        self.isMotionDataUnavailable = true
    }
}
