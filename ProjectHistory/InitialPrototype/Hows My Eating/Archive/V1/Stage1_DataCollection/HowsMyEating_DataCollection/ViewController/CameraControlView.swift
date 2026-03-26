import SwiftUI
import AVFoundation
import QuartzCore

struct CameraControlView: View {
    @StateObject private var cameraManager = CameraManager()
    @StateObject private var motionManager = MotionManager()

    @State private var isRecording: Bool = false
    @State private var timestampString: String = ""
    @State private var currentRecordingFolderURL: URL?
    
    @State private var recordingStartDate: Date?
    @State private var recordingStopDate: Date?
    @State private var recordingStartTime: CMTime?
    @State private var recordingStopTime: CMTime?
    @State private var recordingReferenceTime: Double? = nil

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
        
        // Capture the monotonic reference time for synchronization
        recordingReferenceTime = CACurrentMediaTime()

        // Start recording with reference time for synchronization
        motionManager.startRecording(referenceTime: recordingReferenceTime!)
        cameraManager.startRecording(to: folderURL.appendingPathComponent("\(timestampString).mov"))
        recordingStartDate = Date()
        isRecording = true
    }


    private func stopRecording() async {
        do {
            let motionDataArray = try await motionManager.stopRecording()
            let movie = try await cameraManager.stopRecording()
            recordingStopDate = Date()
         
            // Save motion data as JSON
            if let folderURL = currentRecordingFolderURL {
                let motionFileURL = folderURL.appendingPathComponent("\(timestampString).json")
                let motionData = try JSONEncoder().encode(motionDataArray)
                try motionData.write(to: motionFileURL)
                
                let timestampJsonUrl = folderURL.appendingPathComponent("\(timestampString)_metadata.txt")
                // Metadata includes the shared monotonic recording reference time for synchronization.
                let metadata = [
                    "startDate": self.recordingStartDate?.timeIntervalSince1970 ?? 0.0,
                    "stopDate": self.recordingStopDate?.timeIntervalSince1970 ?? 0.0,
                    "recordingReferenceTime": recordingReferenceTime ?? 0.0,
                ]
                let metadataJsonData = try JSONSerialization.data(withJSONObject: metadata, options: .prettyPrinted)
                try metadataJsonData.write(to: timestampJsonUrl)
            }

        } catch {
            print("Error stopping recording: \(error.localizedDescription)")
        }
        isRecording = false
    }
    
    
}
