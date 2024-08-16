////import UIKit
//
//import SwiftUI
//
//class FileManagerHelper {
//    
//    var selectedData: [CapturedMotionAndMovieData]
//    
//    init(selectedData: [CapturedMotionAndMovieData]) {
//        self.selectedData = selectedData
//    }
//    
//    func createFolderAndShare(in directory: FileManager.SearchPathDirectory, completion: @escaping (URL) -> Void) {
//        let fileManager = FileManager.default
//        let documentsDirectory = fileManager.urls(for: .documentDirectory, in: .userDomainMask).first!
//        let exportDataFolderURL = documentsDirectory.appendingPathComponent("ExportData")
//        
//        do {
//            if !fileManager.fileExists(atPath: exportDataFolderURL.path) {
//                try fileManager.createDirectory(at: exportDataFolderURL, withIntermediateDirectories: true, attributes: nil)
//            }
//            
//            for recordedData in selectedData {
//                let timestampString = formatTimestamp(recordedData.timestamp)
//                let folderURL = exportDataFolderURL.appendingPathComponent(timestampString)  // Append to ExportData folder
//                
//                do {
//                    if !fileManager.fileExists(atPath: folderURL.path) {
//                        try fileManager.createDirectory(at: folderURL, withIntermediateDirectories: true, attributes: nil)
//                    }
//                    
//                    let jsonFileURL = folderURL.appendingPathComponent("\(timestampString).json")
//                    
//                    let motionData = try JSONEncoder().encode(recordedData.motionArray)
//                    try motionData.write(to: jsonFileURL)
//                    
//                    let movieFilePath = documentsDirectory.appendingPathComponent(recordedData.moviePath)
//                    
//                    if fileManager.fileExists(atPath: movieFilePath.path) {
//                        // Use the generateUniqueFileURL method to ensure the destination file name is unique
//                        var movieDestinationPath = folderURL.appendingPathComponent("\(timestampString).mov")
//                        movieDestinationPath = generateUniqueFileURL(for: movieDestinationPath, using: fileManager)
//                        
//                        do {
//                            // Copy the movie file to the unique destination path
//                            try fileManager.copyItem(at: movieFilePath, to: movieDestinationPath)
//                        } catch {
//                            print("Error copying movie file: \(error)")
//                        }
//                    } else {
//                        print("Movie file not found at path: \(movieFilePath.path)")
//                    }
//                    
//                } catch {
//                    print("Error creating folder or file: \(error)")
//                }
//            }
//            
//            // Once all folders are created, pass the ExportData folder URL for sharing
//            completion(exportDataFolderURL)
//            
//        } catch {
//            print("Error creating ExportData folder: \(error)")
//        }
//    }
//    
//    private func generateUniqueFileURL(for url: URL, using fileManager: FileManager) -> URL {
//        var uniqueURL = url
//        var counter = 1
//        
//        while fileManager.fileExists(atPath: uniqueURL.path) {
//            let fileName = url.deletingPathExtension().lastPathComponent
//            let fileExtension = url.pathExtension
//            uniqueURL = url.deletingLastPathComponent().appendingPathComponent("\(fileName)-\(counter).\(fileExtension)")
//            counter += 1
//        }
//        
//        return uniqueURL
//    }
//    
//    private func formatTimestamp(_ date: Date) -> String {
//        let formatter = DateFormatter()
//        formatter.dateFormat = "yyyyMMdd-HHmmss"
//        return formatter.string(from: date)
//    }
//    
//}
