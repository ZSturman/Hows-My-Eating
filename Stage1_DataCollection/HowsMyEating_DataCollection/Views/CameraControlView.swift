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

import SwiftUI
import AVFoundation
import SwiftData

struct CameraControlView: View {
    @Environment(\.modelContext) private var modelContext
    @StateObject private var cameraManager = CameraManager()
    @StateObject private var motionManager = MotionManager()

    @State private var isRecording: Bool = false
    @State private var recordingStartTime: Date? = nil

    var body: some View {
        ZStack {
            CameraView(cameraManager: cameraManager)
                .edgesIgnoringSafeArea(.all)

            VStack {
                Spacer()
                Text(motionManager.isMotionDataUnavailable ? "No motion data available at this time." : "Motion data being recorded")
                    .foregroundColor(.white)
                    .padding()
                    .background(Color.black.opacity(0.7))
                    .cornerRadius(10)
                    .padding()
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
        print("Starting recording...")
        recordingStartTime = Date()
        motionManager.startRecording(startTime: recordingStartTime)
        cameraManager.startRecording(startTime: recordingStartTime)
        isRecording = true
    }

    private func stopRecording() async {
        do {
            let movie = try await cameraManager.stopRecording()
            print("Movie: \(movie)")
            let motionDataArray = try await motionManager.stopRecording()
            print("Motion Data: \(motionDataArray)")

            // Initialize MediaLibrary actor
            let mediaLibrary = MediaLibrary()

            // Save the movie to the app's data directory
            let movieURL = try await mediaLibrary.save(movie: movie)
            let relativeMoviePath = movieURL.lastPathComponent // Save only the relative path
            print("Movie relative path: \(relativeMoviePath)")

            withAnimation {
                // Create a new instance of CapturedMotionAndMovieData with the relative movie path
                let newItem = CapturedMotionAndMovieData(timestamp: recordingStartTime!, motionArray: motionDataArray, moviePath: relativeMoviePath)
                modelContext.insert(newItem)
                print("Saved data: \(newItem)")
            }

        } catch {
            print("Error stopping recording: \(error.localizedDescription)")
        }
        isRecording = false
    }
}
