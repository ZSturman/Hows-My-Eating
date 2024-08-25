import SwiftUI
import AVFoundation



struct CameraControlView: View {
    @StateObject private var cameraManager = CameraManager()
    @StateObject private var motionManager = MotionManager()

    @State private var isRecording: Bool = false
    @State private var timestampString: String = ""
    @State private var currentRecordingFolderURL: URL?
    


    var body: some View {
        
        ZStack {
            CameraView(cameraManager: cameraManager)
                .edgesIgnoringSafeArea(.all)
            
            // Overlay the 3D head model in the top-right corner
            GeometryReader { geometry in
                MotionManagerViewRepresentable(motionManager: motionManager)
                    .frame(width: geometry.size.width / 3, height: geometry.size.height / 3)
                    .position(x: geometry.size.width - geometry.size.width / 6, y: geometry.size.height / 6)
            }

            VStack {
                Spacer()
                
                Button(action: {
                    motionManager.setReferenceFrame()
                }) {
                    Text("Set Reference Frame")
                }

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
        
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyyMMMdd-HHmmss"
        timestampString = formatter.string(from: Date())
        
        // Create the folder for this recording session
        let folderURL = URL.applicationSupportDirectory.appendingPathComponent(timestampString)
        print("Folder URL: \(folderURL)")
        currentRecordingFolderURL = folderURL

        do {
            try FileManager.default.createDirectory(at: folderURL, withIntermediateDirectories: true, attributes: nil)
        } catch {
            print("Error creating recording folder: \(error)")
            return
        }

        // Start recording
        motionManager.startRecording()
        cameraManager.startRecording(to: folderURL.appendingPathComponent("\(timestampString).mov"))
        isRecording = true
    }


    private func stopRecording() async {
        do {
            let movie = try await cameraManager.stopRecording()
            print("Saved movie to \(movie)")
            let motionDataArray = try await motionManager.stopRecording()

            // Save motion data as JSON
            if let folderURL = currentRecordingFolderURL {
                let jsonFileURL = folderURL.appendingPathComponent("\(timestampString).json")
                let motionData = try JSONEncoder().encode(motionDataArray)
                try motionData.write(to: jsonFileURL)
            }

        } catch {
            print("Error stopping recording: \(error.localizedDescription)")
        }
        isRecording = false
    }
    
}
