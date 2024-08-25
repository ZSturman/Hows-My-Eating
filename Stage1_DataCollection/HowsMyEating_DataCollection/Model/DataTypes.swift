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
    var moviePath: String
    
    init(timestamp: Date, motionArray: [MotionData], moviePath: String) {
        self.timestamp = timestamp
        self.motionArray = motionArray
        self.moviePath = moviePath
    }
}


struct MotionData: Codable {
    var timestamp: Date
    var attitude: Attitude
    var rotationRate: RotationRate
    var userAcceleration: UserAcceleration
    var gravity: Gravity
    let transformedRotation: TransformedRotation

    init(timestamp: Date, attitude: Attitude, rotationRate: RotationRate, userAcceleration: UserAcceleration, gravity: Gravity, transformedRotation: TransformedRotation) {
        self.timestamp = timestamp
        self.attitude = attitude
        self.rotationRate = rotationRate
        self.userAcceleration = userAcceleration
        self.gravity = gravity
        self.transformedRotation = transformedRotation
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

struct TransformedRotation: Codable {
    let x: Double
    let y: Double
    let z: Double
    let w: Double
    
    static let zero = TransformedRotation(x: 0.0, y: 0.0, z: 0.0, w: 0.0)
}

var defaultMotionData = MotionData(timestamp: .now, attitude: .zero, rotationRate: .zero, userAcceleration: .zero, gravity: .zero, transformedRotation: .zero)

extension float4x4 {
    init(rotationMatrix r: CMRotationMatrix) {
        self.init([
            simd_float4(Float(-r.m11), Float(r.m13), Float(r.m12), 0.0),
            simd_float4(Float(-r.m31), Float(r.m33), Float(r.m32), 0.0),
            simd_float4(Float(-r.m21), Float(r.m23), Float(r.m22), 0.0),
            simd_float4(          0.0,          0.0,          0.0, 1.0)
        ])
    }
}
