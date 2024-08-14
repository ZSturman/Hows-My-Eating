//
//  MotionManager.swift
//  HowsMyEating_DataCollection
//
//  Created by Zachary Sturman on 8/14/24.
//


import Combine
import CoreMotion
import SwiftUI

final class MotionManager: NSObject, ObservableObject, CMHeadphoneMotionManagerDelegate {
    private var manager: CMHeadphoneMotionManager = CMHeadphoneMotionManager()
    private var motionQueue = OperationQueue()
    private var motionTimer: Timer?
    
    
    @Published var connectionStatus: Bool = false
    @Published var motionDataAvailable: Bool = false
    
    private(set) var motionDataArray: [MotionData] = []
    var recordingStartTime: TimeInterval?
    
    
    override init() {
        super.init()
        manager.delegate = self
        checkMotionDataAvailability()

    }
    
    func checkMotionDataAvailability() {
        self.motionDataAvailable = manager.isDeviceMotionAvailable
        print("Motion data availability: \(self.motionDataAvailable)")
    }
    
    func restartMotionUpdates() {
        print("Restarting motion updates due to initial values being zero.")
        manager.stopDeviceMotionUpdates()
        manager.startDeviceMotionUpdates()
    }
    
    func verifyInitialUpdates() {
        if manager.isDeviceMotionAvailable {
            print("Device motion is available. Starting device motion updates for verification.")
            manager.startDeviceMotionUpdates()
        } else {
            print("Device motion is not available.")
            connectionStatus = false
        }
    }
    
    
    
    func startRecording() {
        self.recordingStartTime = Date().timeIntervalSince1970
        self.motionDataArray = [] // Reset motion data array
        
        manager.startDeviceMotionUpdates()
        if manager.isDeviceMotionAvailable {
            print("Device motion is available. Starting device motion updates.")
            
            
            motionTimer = Timer.scheduledTimer(withTimeInterval: 1.0 / 200.0, repeats: true) { _ in
                self.collectMotionData()
            }
            
        } else {
            print("Device motion is not available.")
            connectionStatus = false
        }
    }
    

    
    
    
    private func collectMotionData() {
        if let motion = manager.deviceMotion {
            let attitude = Attitude(roll: motion.attitude.roll, pitch: motion.attitude.pitch, yaw: motion.attitude.yaw)
            let rotationRate = RotationRate(x: motion.rotationRate.x, y: motion.rotationRate.y, z: motion.rotationRate.z)
            let userAcceleration = UserAcceleration(x: motion.userAcceleration.x, y: motion.userAcceleration.y, z: motion.userAcceleration.z)
            let gravity = Gravity(x: motion.gravity.x, y: motion.gravity.y, z: motion.gravity.z)
            
            let relativeTimestamp = Date().timeIntervalSince1970 - (self.recordingStartTime ?? 0)
            
            let motionElement = MotionData(
                timestamp: relativeTimestamp,
                attitude: attitude,
                rotationRate: rotationRate,
                userAcceleration: userAcceleration,
                gravity: gravity
            )
            
            DispatchQueue.main.async {
                self.motionDataArray.append(motionElement)
            }
        }
    }
    

    func stopRecording() async throws -> [MotionData] {
        motionTimer?.invalidate()
        motionTimer = nil
        manager.stopDeviceMotionUpdates()
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

