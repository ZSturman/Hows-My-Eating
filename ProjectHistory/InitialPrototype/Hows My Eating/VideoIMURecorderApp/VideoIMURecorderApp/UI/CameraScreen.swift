//
//  CameraScreen.swift
//  VideoIMURecorderApp
//
//  Created by Zachary Sturman on 11/12/25.
//

import SwiftUI
import AVKit

struct CameraScreen: View {
    @ObservedObject var controller: RecorderController
    var onDone: (URL?) -> Void
    @Environment(\.dismiss) private var dismiss

    init(controller: RecorderController, onDone: @escaping (URL?) -> Void = { _ in }) {
        self.controller = controller
        self.onDone = onDone
    }

    var body: some View {
        ZStack(alignment: .topLeading) {
            if let session = controller.captureSession {
                CameraPreviewView(session: session)
                    .ignoresSafeArea()
            } else {
                Color.black.ignoresSafeArea()
                Text("Camera preview")
                    .foregroundColor(.white.opacity(0.7))
            }

            VStack {
                Spacer()
                statusBar
                controls
            }
            .padding(.bottom, 24)
            .padding(.horizontal, 16)
        }
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                RoutePickerView()
                    .frame(width: 44, height: 44)
                    .foregroundColor(.white)
            }
        }
        .onAppear {
            controller.prepare()
            controller.startCameraPreview()
        }
        .onDisappear {
            controller.stopCameraPreview()
            onDone(controller.lastSessionFolder)
            dismiss()
        }
    }


    private var statusBar: some View {
        HStack(spacing: 12) {
            if let motion = controller.latestMotion {
                Text(String(format: "ax: %.2f, ay: %.2f, az: %.2f", motion.ax, motion.ay, motion.az))
                    .font(.system(.callout, design: .rounded))
                    .foregroundColor(.white)
            } else {
                Text("No motion data")
                    .font(.system(.callout, design: .rounded))
                    .foregroundColor(.yellow)
            }

            Circle()
                .fill(controller.isRecording ? Color.red : Color.gray.opacity(0.6))
                .frame(width: 10, height: 10)
            Text(controller.statusText)
                .font(.system(.callout, design: .rounded))
                .foregroundColor(.white)
            Spacer()
        }
        .padding(10)
        .background(.ultraThinMaterial, in: Capsule())
    }

    private var controls: some View {
        VStack(spacing: 8) {
            Group {
                HStack(spacing: 12) {
                    if controller.isRecording {
                        Button(action: controller.stop) {
                            Text("Stop")
                                .font(.system(.title2, design: .rounded).bold())
                                .padding(.horizontal, 28)
                                .padding(.vertical, 12)
                                .background(Color.red)
                                .foregroundColor(.white)
                                .clipShape(Capsule())
                        }
                    } else if controller.isPaused {
                        Button(action: { controller.cancelPausedRecording() }) {
                            Text("Cancel")
                                .font(.system(.title3, design: .rounded).bold())
                                .padding(.horizontal, 18)
                                .padding(.vertical, 12)
                                .background(Color.gray)
                                .foregroundColor(.white)
                                .clipShape(Capsule())
                        }

                        Button(action: { controller.resumeAfterMotionReturns() }) {
                            Text("Resume")
                                .font(.system(.title3, design: .rounded).bold())
                                .padding(.horizontal, 18)
                                .padding(.vertical, 12)
                                .background(Color.green)
                                .foregroundColor(.white)
                                .clipShape(Capsule())
                        }
                        .disabled(!controller.canResumeRecording)
                    } else {
                        Button(action: { controller.start(withLabel: true) }) {
                            Text("Eating")
                                .font(.system(.title3, design: .rounded).bold())
                                .padding(.horizontal, 18)
                                .padding(.vertical, 12)
                                .background(Color.green)
                                .foregroundColor(.white)
                                .clipShape(Capsule())
                        }
                        .disabled(!controller.isMotionAvailable)

                        Button(action: { controller.start(withLabel: false) }) {
                            Text("Not Eating")
                                .font(.system(.title3, design: .rounded).bold())
                                .padding(.horizontal, 18)
                                .padding(.vertical, 12)
                                .background(Color.blue)
                                .foregroundColor(.white)
                                .clipShape(Capsule())
                        }
                        .disabled(!controller.isMotionAvailable)
                    }
                }
            }
            .opacity((controller.isMotionAvailable || controller.isRecording || controller.isPaused) ? 1.0 : 0.4)

            if !controller.isMotionAvailable && !controller.isRecording {
                HStack(spacing: 6) {
                    Image(systemName: "headphones")
                    Text("Connect AirPods to begin")
                }
                .font(.footnote)
                .foregroundColor(.yellow)
                .padding(.top, 2)
            }
        }
    }
}
