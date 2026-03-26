//
//  CameraPreviewView.swift
//  VideoIMURecorderApp
//
//  Created by Zachary Sturman on 9/7/25.
//

import Foundation
import SwiftUI
import AVFoundation

struct CameraPreviewView: UIViewRepresentable {
    let session: AVCaptureSession

    func makeUIView(context: Context) -> Preview {
        let v = Preview()
        v.videoPreviewLayer.session = session
        v.videoPreviewLayer.videoGravity = .resizeAspectFill
        return v
    }

    func updateUIView(_ uiView: Preview, context: Context) {
        if let connection = uiView.videoPreviewLayer.connection {
            if #available(iOS 17.0, *) {
                // Rotate the camera preview to portrait orientation and match the video output.
                connection.videoRotationAngle = 90
            } else {
                connection.videoOrientation = .portrait
            }
        }
    }

    final class Preview: UIView {
        override class var layerClass: AnyClass { AVCaptureVideoPreviewLayer.self }
        var videoPreviewLayer: AVCaptureVideoPreviewLayer { layer as! AVCaptureVideoPreviewLayer }
    }
}
