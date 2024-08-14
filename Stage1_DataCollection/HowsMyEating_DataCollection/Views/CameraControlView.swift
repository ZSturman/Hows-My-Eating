import SwiftUI
import AVFoundation
import SwiftData

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
struct CameraControlView: View {
    @Environment(\.modelContext) private var modelContext
    @StateObject private var cameraManager = CameraManager()
    @StateObject private var motionManager = MotionManager()
    
    @State private var isRecording: Bool = false
    
    var body: some View {
        ZStack {
            CameraView(cameraManager: cameraManager)
                .edgesIgnoringSafeArea(.all)
            
            VStack {
                Spacer()
                HStack {
                    Spacer()
                    Button(action: {
                        if isRecording {
                            Task {
                                await stopRecording()
                            }
                        } else {
                            startRecording()
                        }
                    }) {
                        Text(isRecording ? "Stop Recording" : "Start Recording")
                            .foregroundColor(.white)
                            .padding()
                            .background(isRecording ? Color.red : Color.green)
                            .cornerRadius(10)
                    }
                    Spacer()
                }
                .padding()
            }
        }
    }
    
    private func startRecording() {
        cameraManager.startRecording()
        motionManager.startRecording()
        isRecording = true
    }
    
    private func stopRecording() async {
        do {
            let movie = try await cameraManager.stopRecording()
            let motionDataArray = try await motionManager.stopRecording()
            
            withAnimation {
                let newItem = CapturedMotionAndMovieData(timestamp: Date(), motionArray: motionDataArray, moviePath: movie.url)
                modelContext.insert(newItem)
            }
        } catch {
            print("Error stopping recording: \(error.localizedDescription)")
        }
        isRecording = false
    }
}
