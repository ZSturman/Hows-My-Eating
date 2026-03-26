//
//  ContentView.swift
//  HowsMyEating
//
//  Created by Zachary Sturman on 2/7/25.
//

import SwiftUI

struct ContentView: View {
    @StateObject private var motionManager = MotionManager()
    
    var body: some View {
        VStack(spacing: 20) {
            Text("Chewing Prediction:")
                .font(.title2)
            
            Text(motionManager.chewingPrediction)
                .font(.largeTitle)
                .bold()
            
            if motionManager.connectionStatus {
                Text("AirPods Connected")
                    .foregroundColor(.green)
            } else {
                Text("AirPods Not Connected")
                    .foregroundColor(.red)
            }
            
            if motionManager.isMotionDataUnavailable {
                Text("Motion Data Unavailable")
                    .foregroundColor(.orange)
            } else {
                Text("Motion Data Available")
                    .foregroundColor(.blue)
            }
            
            // Display live motion data
            VStack(spacing: 10) {
                Text("Rotation Rate:")
                    .font(.headline)
                Text("X: \(motionManager.liveRotationRate.x, specifier: "%.2f")")
                Text("Y: \(motionManager.liveRotationRate.y, specifier: "%.2f")")
                Text("Z: \(motionManager.liveRotationRate.z, specifier: "%.2f")")
                
                Text("User Acceleration:")
                    .font(.headline)
                Text("X: \(motionManager.liveUserAcceleration.x, specifier: "%.2f")")
                Text("Y: \(motionManager.liveUserAcceleration.y, specifier: "%.2f")")
                Text("Z: \(motionManager.liveUserAcceleration.z, specifier: "%.2f")")
                
                Text("Attitude:")
                    .font(.headline)
                Text("Roll: \(motionManager.liveAttitude.roll, specifier: "%.2f")")
                Text("Pitch: \(motionManager.liveAttitude.pitch, specifier: "%.2f")")
                Text("Yaw: \(motionManager.liveAttitude.yaw, specifier: "%.2f")")
            }
        }
        .padding()
        .onAppear {
            motionManager.startRecording()
        }
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}
