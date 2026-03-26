import SwiftUI
import UIKit
import UniformTypeIdentifiers
import Foundation


struct ContentView: View {
    @State var contentFolder = URL.applicationSupportDirectory
    @State var recordingFolders: [URL] = []
    @State var selectedFolder: URL?
    @State private var showActivityView = false

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

                if recordingFolders.isEmpty {
                    Text("No recorded data")
                        .padding()
                } else {
                    List {
                        ForEach(recordingFolders, id: \.self) { folder in
                            HStack {
                                Text(folder.lastPathComponent)
                                Spacer()
                                if selectedFolder == folder {
                                    Image(systemName: "checkmark")
                                        .foregroundColor(.blue)
                                }
                            }
                            .contentShape(Rectangle())
                            .onTapGesture {
                                toggleSelection(for: folder)
                            }
                        }
                        .onDelete(perform: deleteItems)
                    }
                }
            }
            .navigationTitle("How's My Eating? Data Collection")
            .padding()
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        showActivityView = true
                    }) {
                        Text("Share")
                    }
                    .disabled(selectedFolder == nil)
                }
            }
            .sheet(isPresented: $showActivityView) {
                if let folder = selectedFolder {
                    ActivityViewController(folderURL: folder) {
                        showDeleteConfirmation(for: folder)
                    }
                }
            }
            .onAppear {
                loadFolders()
            }
        }
    }

    private func loadFolders() {
        do {
            let folderURLs = try FileManager.default.contentsOfDirectory(at: contentFolder, includingPropertiesForKeys: nil, options: [.skipsHiddenFiles])
            recordingFolders = folderURLs.filter { $0.hasDirectoryPath }
        } catch {
            print("Error loading recording folders: \(error)")
        }
    }
    

    private func toggleSelection(for folder: URL) {
        if selectedFolder == folder {
            selectedFolder = nil
        } else {
            selectedFolder = folder
        }
    }

    private func deleteItems(offsets: IndexSet) {
        withAnimation {
            for index in offsets {
                let folder = recordingFolders[index]
                do {
                    try FileManager.default.removeItem(at: folder)
                    recordingFolders.remove(at: index)
                } catch {
                    print("Error deleting folder: \(error)")
                }
            }
        }
    }
    
    private func showDeleteConfirmation(for folderURL: URL) {
        let alertController = UIAlertController(title: "Folder Shared", message: "Do you want to delete the folder?", preferredStyle: .alert)
        let deleteAction = UIAlertAction(title: "Delete", style: .destructive) { _ in
            do {
                try FileManager.default.removeItem(at: folderURL)
                print("Folder deleted.")
                loadFolders()
            } catch {
                print("Error deleting folder: \(error)")
            }
        }
        let keepAction = UIAlertAction(title: "Keep", style: .cancel, handler: nil)
        
        alertController.addAction(deleteAction)
        alertController.addAction(keepAction)
        
        if let windowScene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
           let rootViewController = windowScene.windows.first?.rootViewController {
            rootViewController.present(alertController, animated: true, completion: nil)
        }
    }
}


