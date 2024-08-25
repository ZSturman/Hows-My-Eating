import Foundation
import CoreMotion
import SwiftUI
import SceneKit
import simd

final class MotionManager: NSObject, ObservableObject, CMHeadphoneMotionManagerDelegate {
    private var manager: CMHeadphoneMotionManager = CMHeadphoneMotionManager()

    @Published var connectionStatus: Bool = false
    @Published var motionDataAvailable: Bool = false
    @Published var isMotionDataUnavailable: Bool = false

    private(set) var motionDataArray: [MotionData] = []
    private var referenceFrame = matrix_identity_float4x4
    private var referenceFrameHasChanged: Bool = false

    var onMotionUpdate: ((float4x4, float4x4) -> Void)?

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

        onMotionUpdate?(rotation, referenceFrame)

        let motionElement = MotionData(
            timestamp: Date(),
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
