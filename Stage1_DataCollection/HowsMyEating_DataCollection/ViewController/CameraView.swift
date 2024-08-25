//
//  CameraView.swift
//  HowsMyEating_DataCollection
//
//  Created by Zachary Sturman on 8/25/24.
//

import Foundation
import SwiftUI

struct CameraView: UIViewControllerRepresentable {
    @ObservedObject var cameraManager = CameraManager()

    
    func makeUIViewController(context: Context) -> UIViewController {
        let viewController = UIViewController()
        cameraManager.setupCamera()
        cameraManager.startPreview(in: viewController.view)
        return viewController
    }
    
    func updateUIViewController(_ uiViewController: UIViewController, context: Context) { }
}
