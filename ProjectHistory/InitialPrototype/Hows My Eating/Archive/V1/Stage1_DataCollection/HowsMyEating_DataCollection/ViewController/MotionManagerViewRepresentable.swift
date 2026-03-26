import Foundation
import SwiftUI
import UIKit
import SceneKit
import CoreMotion
import simd

struct MotionManagerViewRepresentable: UIViewControllerRepresentable {
    @ObservedObject var motionManager: MotionManager
    
    func makeUIViewController(context: Context) -> UIViewController {
        let viewController = UIViewController()
        setupSceneView(in: viewController.view)
        return viewController
    }
    
    func updateUIViewController(_ uiViewController: UIViewController, context: Context) {
        // You can update your view controller based on the state of the motionManager
    }
    
    private func setupSceneView(in view: UIView) {
        let sceneView = SCNView(frame: view.bounds)
        sceneView.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        sceneView.backgroundColor = UIColor.clear  // Set SCNView background to transparent
        view.addSubview(sceneView)
        
        // Setup the scene here
        let scene = SCNScene(named: "head.obj")!
        scene.background.contents = UIColor.clear // Ensure the scene's background is also transparent
        
        let headNode = scene.rootNode.childNodes.first
        
        let cameraNode = SCNNode()
        cameraNode.camera = SCNCamera()
        scene.rootNode.addChildNode(cameraNode)
        
        cameraNode.position = SCNVector3(x: 0, y: 0, z: 2.0)
        cameraNode.camera?.zNear = 0.05
        
        let lightNode = SCNNode()
        lightNode.light = SCNLight()
        lightNode.light!.type = .omni
        lightNode.position = SCNVector3(x: 0, y: 10, z: 10)
        scene.rootNode.addChildNode(lightNode)
        
        let ambientLightNode = SCNNode()
        ambientLightNode.light = SCNLight()
        ambientLightNode.light!.type = .ambient
        ambientLightNode.light!.color = UIColor.darkGray
        scene.rootNode.addChildNode(ambientLightNode)
        
        sceneView.scene = scene
        
        // Bind the scene to the MotionManager's updates
        motionManager.onMotionUpdate = { rotation, referenceFrame in
            headNode?.simdTransform = simd_float4x4([
                simd_float4(-1.0, 0.0, 0.0, 0.0),
                simd_float4( 0.0, 1.0, 0.0, 0.0),
                simd_float4( 0.0, 0.0, 1.0, 0.0),
                simd_float4( 0.0, 0.0, 0.0, 1.0)
            ]) * rotation * referenceFrame
        }
    }
}
