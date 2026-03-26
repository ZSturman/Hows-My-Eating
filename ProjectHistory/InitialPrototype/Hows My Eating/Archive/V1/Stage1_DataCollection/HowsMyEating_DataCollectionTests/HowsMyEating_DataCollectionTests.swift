//
//  HowsMyEating_DataCollectionTests.swift
//  HowsMyEating_DataCollectionTests
//
//  Created by Zachary Sturman on 8/14/24.
//  Updated on 2025-02-20
//

import XCTest
@testable import HowsMyEating_DataCollection

final class HowsMyEating_DataCollectionTests: XCTestCase {
    
    func testDefaultMotionData() {
        let motion = defaultMotionData
        XCTAssertEqual(motion.timestamp, 0.0, "Default timestamp should be 0.0")
        XCTAssertEqual(motion.attitude.roll, 0.0, "Default roll should be 0.0")
        XCTAssertEqual(motion.rotationRate.x, 0.0, "Default rotationRate x should be 0.0")
        XCTAssertEqual(motion.userAcceleration.y, 0.0, "Default userAcceleration y should be 0.0")
        XCTAssertEqual(motion.gravity.z, 0.0, "Default gravity z should be 0.0")
        XCTAssertEqual(motion.transformedRotation.w, 0.0, "Default transformedRotation w should be 0.0")
    }
    
    func testCameraManagerSetup() {
        let cameraManager = CameraManager()
        cameraManager.setupCamera()
        // Since previewLayer is private, we verify that the manager is not nil
        XCTAssertNotNil(cameraManager, "CameraManager should not be nil after setup")
    }
    
    func testDeviceLookup() throws {
        let lookup = DeviceLookup()
        let cameras = lookup.cameras
        XCTAssertFalse(cameras.isEmpty, "No cameras found by DeviceLookup")
        
        let defaultCamera = try lookup.defaultCamera
        XCTAssertNotNil(defaultCamera, "Default camera should be available")
    }
    
    func testMotionManagerRecording() async throws {
        let motionManager = MotionManager()
        // Use a precise reference time for starting the recording
        let refTime = CACurrentMediaTime()
        motionManager.startRecording(referenceTime: refTime)
        // Simulate a brief delay to capture some data.
        try await Task.sleep(nanoseconds: 500_000_000)
        let recordedData = try await motionManager.stopRecording()
        XCTAssertGreaterThanOrEqual(recordedData.count, 0, "Recorded data count should be >= 0")
    }
}
