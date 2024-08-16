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
    @StateObject private var cameraManager = CameraManager()
    @StateObject private var motionManager = MotionManager()

    @State private var isRecording: Bool = false
    @State private var recordingStartTime: Date? = nil
    @State private var currentRecordingFolderURL: URL?

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
        
        // Create the folder for this recording session
        let timestampString = formatTimestamp(recordingStartTime!)
        let folderURL = URL.applicationSupportDirectory.appendingPathComponent(timestampString)
        currentRecordingFolderURL = folderURL

        do {
            try FileManager.default.createDirectory(at: folderURL, withIntermediateDirectories: true, attributes: nil)
        } catch {
            print("Error creating recording folder: \(error)")
            return
        }

        // Start recording
        motionManager.startRecording(startTime: recordingStartTime)
        cameraManager.startRecording(to: folderURL.appendingPathComponent("\(timestampString).mov"), startTime: recordingStartTime)
        isRecording = true
    }

    private func stopRecording() async {
        do {
            let movie = try await cameraManager.stopRecording()
            print("Saved movie to \(movie)")
            let motionDataArray = try await motionManager.stopRecording()

            // Save motion data as JSON
            if let folderURL = currentRecordingFolderURL {
                let jsonFileURL = folderURL.appendingPathComponent("\(formatTimestamp(recordingStartTime!)).json")
                let motionData = try JSONEncoder().encode(motionDataArray)
                try motionData.write(to: jsonFileURL)
            }

        } catch {
            print("Error stopping recording: \(error.localizedDescription)")
        }
        isRecording = false
    }
    
    private func formatTimestamp(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyyMMdd-HHmmss"
        return formatter.string(from: date)
    }
}
