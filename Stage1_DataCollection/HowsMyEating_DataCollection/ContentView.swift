import SwiftUI
import SwiftData
import UniformTypeIdentifiers

struct ContentView: View {
    @Environment(\.modelContext) private var modelContext
    @Query var recordedDataList: [CapturedMotionAndMovieData]
    
    @State private var isShowingExportSheet = false
    @State private var exportURL: URL?

    var body: some View {
        NavigationView {
            VStack {
                NavigationLink(destination: CameraControlView()) {
                    Text("Record New Data")
                        .padding()
                        .background(Color.blue)
                        .foregroundColor(.white)
                        .cornerRadius(8)
                }
                .padding()
                
                if recordedDataList.isEmpty {
                    Text("No recorded data")
                        .padding()
                } else {
                    List {
                        ForEach(recordedDataList) { recordedData in
                            NavigationLink(destination: DetailedRecordingView(recordedData: recordedData)) {
                                Text("Data: \(recordedData.timestamp)")
                            }
                            .padding()
                        }
                        .onDelete(perform: deleteItems)
                    }
                    
                    // Export Button
                    Button(action: exportData) {
                        Text("Export All Data")
                            .foregroundColor(.white)
                            .padding()
                            .background(Color.green)
                            .cornerRadius(8)
                    }
                    .padding()
                    .sheet(isPresented: $isShowingExportSheet, content: {
                        if let exportURL = exportURL {
                            ActivityView(activityItems: [exportURL])
                        }
                    })
                }
            }
            .navigationTitle("How's My Eating? Data Collection")
            .padding()
        }
    }

    private func deleteItems(offsets: IndexSet) {
        withAnimation {
            for index in offsets {
                modelContext.delete(recordedDataList[index])
            }
        }
    }
    
    private func exportData() {
        let fileManager = FileManager.default
        let tempDirectory = fileManager.temporaryDirectory
        let exportDirectory = tempDirectory.appendingPathComponent("ExportedData")
        let uniqueZipFilename = "ExportedData-\(UUID().uuidString).zip"
        let zipFilePath = tempDirectory.appendingPathComponent(uniqueZipFilename)
        
        do {
            // Create directory for export
            try fileManager.createDirectory(at: exportDirectory, withIntermediateDirectories: true, attributes: nil)
            
            for recordedData in recordedDataList {
                let dataFilePath = exportDirectory.appendingPathComponent("\(recordedData.timestamp).json")
                let documentsDirectory = fileManager.urls(for: .documentDirectory, in: .userDomainMask).first!
                let movieFilePath = documentsDirectory.appendingPathComponent(recordedData.moviePath)
                
                // Save motion data as JSON
                let motionData = try JSONEncoder().encode(recordedData.motionArray)
                try motionData.write(to: dataFilePath)
                
                // Verify that the movie file exists before copying
                if fileManager.fileExists(atPath: movieFilePath.path) {
                    print("Found \(movieFilePath)")
                    try fileManager.copyItem(at: movieFilePath, to: exportDirectory.appendingPathComponent(recordedData.moviePath))
                } else {
                    print("Movie file not found at path: \(movieFilePath.path)")
                }
                
            }
            
            // Create ZIP archive
            try fileManager.zipItem(at: exportDirectory, to: zipFilePath)
            
            // Set export URL for sharing
            exportURL = zipFilePath
            isShowingExportSheet = true
            
            // Cleanup
            try fileManager.removeItem(at: exportDirectory)
        } catch {
            print("Error exporting data: \(error.localizedDescription)")
        }
    }
}

// ActivityView for sharing
struct ActivityView: UIViewControllerRepresentable {
    var activityItems: [Any]
    
    func makeUIViewController(context: Context) -> UIActivityViewController {
        return UIActivityViewController(activityItems: activityItems, applicationActivities: nil)
    }
    
    func updateUIViewController(_ uiViewController: UIActivityViewController, context: Context) {}
}

extension FileManager {
    func zipItem(at sourceURL: URL, to destinationURL: URL) throws {
        let coordinator = NSFileCoordinator()
        var zipError: Error?
        coordinator.coordinate(readingItemAt: sourceURL, options: [.forUploading], error: nil) { (zipURL) in
            do {
                try self.moveItem(at: zipURL, to: destinationURL)
            } catch {
                zipError = error
            }
        }
        if let error = zipError {
            throw error
        }
    }
}

//
//#Preview {
//    ContentView()
//        .modelContainer(for: Item.self, inMemory: true)
//}
