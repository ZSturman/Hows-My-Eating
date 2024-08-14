//
//  DataTypes.swift
//  HowsMyEating_DataCollection
//
//  Created by Zachary Sturman on 8/14/24.
//

import AVFoundation
import Foundation
import SwiftData
import CoreMotion


/// An enumeration that describes the current status of the camera.
enum CameraStatus {
    /// The initial status upon creation.
    case unknown
    /// A status that indicates a person disallows access to the camera or microphone.
    case unauthorized
    /// A status that indicates the camera failed to start.
    case failed
    /// A status that indicates the camera is successfully running.
    case running
    /// A status that indicates higher-priority media processing is interrupting the camera.
    case interrupted
}

enum CameraError: Error {
    case videoDeviceUnavailable
    case audioDeviceUnavailable
    case addInputFailed
    case addOutputFailed
    case setupFailed
    case deviceChangeFailed
}

/// A structure that contains the uniform type identifier and movie URL.
struct Movie: Sendable {
    /// The temporary location of the file on disk.
    let url: URL
}




@Model
final class CapturedMotionAndMovieData {
    var timestamp: Date
    var motionArray: [MotionData]
    var moviePath: URL
    
    init(timestamp: Date, motionArray: [MotionData], moviePath: URL) {
        self.timestamp = timestamp
        self.motionArray = motionArray
        self.moviePath = moviePath
    }
}


struct MotionData: Codable {
    var timestamp: TimeInterval
    var attitude: Attitude
    var rotationRate: RotationRate
    var userAcceleration: UserAcceleration
    var gravity: Gravity

    init(timestamp: TimeInterval, attitude: Attitude, rotationRate: RotationRate, userAcceleration: UserAcceleration, gravity: Gravity) {
        self.timestamp = timestamp
        self.attitude = attitude
        self.rotationRate = rotationRate
        self.userAcceleration = userAcceleration
        self.gravity = gravity
    }
    
}


struct Attitude: Codable {
     let roll: Double
     let pitch: Double
     let yaw: Double
    
    static let zero = Attitude(roll: 0.0, pitch: 0.0, yaw: 0.0)
 }

struct RotationRate: Codable {
    let x: Double
    let y: Double
    let z: Double
    
    static let zero = RotationRate(x: 0.0, y: 0.0, z: 0.0)
}

struct Gravity: Codable {
    let x: Double
    let y: Double
    let z: Double
    
    static let zero = Gravity(x: 0.0, y: 0.0, z: 0.0)
}


struct UserAcceleration: Codable {
    let x: Double
    let y: Double
    let z: Double
    
    static let zero = UserAcceleration(x: 0.0, y: 0.0, z: 0.0)
}

var defaultMotionData = MotionData(timestamp: 0.0, attitude: .zero, rotationRate: .zero, userAcceleration: .zero, gravity: .zero)
