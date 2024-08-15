import Combine
import CoreMotion
import SwiftUI

final class MotionManager: NSObject, ObservableObject, CMHeadphoneMotionManagerDelegate {
    private var manager: CMHeadphoneMotionManager = CMHeadphoneMotionManager()
    private var motionQueue = OperationQueue()
    private var motionTimer: Timer?

    @Published var connectionStatus: Bool = false
    @Published var motionDataAvailable: Bool = false
    @Published var isMotionDataUnavailable: Bool = false  // New boolean to track motion data availability status

    private(set) var motionDataArray: [MotionData] = []
    var recordingStartTime: Date?

    override init() {
        super.init()
        manager.delegate = self
        checkMotionDataAvailability()
    }

    func checkMotionDataAvailability() {
        self.motionDataAvailable = manager.isDeviceMotionAvailable
        print("Motion data availability: \(self.motionDataAvailable)")
        manager.startDeviceMotionUpdates()
        previewMotionData()
    }

    private func previewMotionData() {
        if let motion = manager.deviceMotion {
            print("Motion data: \(motion)")
        }
    }

    func startRecording(startTime: Date?) {
        self.recordingStartTime = startTime
        self.motionDataArray = []
        self.isMotionDataUnavailable = false  // Reset the status at the start

        manager.startDeviceMotionUpdates()
        if manager.isDeviceMotionAvailable {
            print("Device motion is available. Starting device motion updates.")

            DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
                self.motionTimer = Timer.scheduledTimer(withTimeInterval: 1.0 / 200.0, repeats: true) { _ in
                    self.collectMotionData()
                }
            }
        } else {
            print("Device motion is not available.")
            connectionStatus = false
            self.isMotionDataUnavailable = true
        }
    }

    private func collectMotionData() {
        if let motion = manager.deviceMotion, let startTime = recordingStartTime {
            let attitude = Attitude(roll: motion.attitude.roll, pitch: motion.attitude.pitch, yaw: motion.attitude.yaw)
            let rotationRate = RotationRate(x: motion.rotationRate.x, y: motion.rotationRate.y, z: motion.rotationRate.z)
            let userAcceleration = UserAcceleration(x: motion.userAcceleration.x, y: motion.userAcceleration.y, z: motion.userAcceleration.z)
            let gravity = Gravity(x: motion.gravity.x, y: motion.gravity.y, z: motion.gravity.z)

            let relativeTimestamp = Date().timeIntervalSince(startTime)

            let motionElement = MotionData(
                timestamp: relativeTimestamp,
                attitude: attitude,
                rotationRate: rotationRate,
                userAcceleration: userAcceleration,
                gravity: gravity
            )

            DispatchQueue.main.async {
                self.motionDataArray.append(motionElement)
                print("Collected motion data: \(motionElement)")
                self.isMotionDataUnavailable = false
            }
        } else {
            print("No motion data available at this time.")
            self.isMotionDataUnavailable = true  // Update the status if no data is available
        }
    }

    func stopRecording() async throws -> [MotionData] {
        motionTimer?.invalidate()
        motionTimer = nil
        manager.stopDeviceMotionUpdates()
        print("Final motion data count: \(motionDataArray.count)")
        return motionDataArray
    }

    func reset() {
        recordingStartTime = nil
        motionDataArray = []
    }

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
}
