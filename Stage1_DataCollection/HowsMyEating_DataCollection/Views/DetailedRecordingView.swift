//
//  DetailedRecordingView.swift
//  HowsMyEating_DataCollection
//
//  Created by Zachary Sturman on 8/14/24.
//
import Foundation
import SwiftData
import SwiftUI
import AVKit
import AVFoundation

struct DetailedRecordingView: View {
    @Environment(\.modelContext) private var modelContext
    var recordedData: CapturedMotionAndMovieData
    
    @State private var isShowingVideoPlayer: Bool = false
    @State private var showAlert: Bool = false
    @State private var alertMessage: String = ""

    var body: some View {
        VStack {
            Text("Motion Data Details")
                .font(.headline)
                .padding()
            
            // Display the number of motion data samples collected
            Text("Number of motion data samples: \(recordedData.motionArray.count)")
                .padding()
            
            // Display the file path of the saved movie
            Text("Recorded Movie Path:")
                .font(.subheadline)
                .padding(.top)
            Text("\(recordedData.moviePath)")
                .padding(.bottom)
            
            let documentsDirectory = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
            let fullMoviePath = documentsDirectory.appendingPathComponent(recordedData.moviePath)
            
            // Button to play the video
            Button(action: {
                if FileManager.default.fileExists(atPath: fullMoviePath.path) {
                    isShowingVideoPlayer.toggle()
                } else {
                    alertMessage = "Movie file not found at path: \(fullMoviePath.path)"
                    showAlert = true
                }
            }) {
                Text("Play Video")
                    .foregroundColor(.white)
                    .padding()
                    .background(Color.blue)
                    .cornerRadius(10)
            }
            .padding()
            .fullScreenCover(isPresented: $isShowingVideoPlayer) {
                VideoPlayerView(videoURL: fullMoviePath)
            }
            .alert(isPresented: $showAlert) {
                Alert(title: Text("Error"), message: Text(alertMessage), dismissButton: .default(Text("OK")))
            }
            
            Spacer()
        }
        .navigationBarTitle("Recording Details", displayMode: .inline)
        .padding()
    }
}

struct VideoPlayerView: View {
    let videoURL: URL
    
    var body: some View {
        AVPlayerViewControllerRepresented(player: AVPlayer(url: videoURL))
            .edgesIgnoringSafeArea(.all)
    }
}

struct AVPlayerViewControllerRepresented: UIViewControllerRepresentable {
    let player: AVPlayer
    
    func makeUIViewController(context: Context) -> AVPlayerViewController {
        let controller = AVPlayerViewController()
        controller.player = player
        controller.modalPresentationStyle = .fullScreen // Ensure the video player is full screen
        return controller
    }
    
    func updateUIViewController(_ uiViewController: AVPlayerViewController, context: Context) {
        // No need to update the view controller in this case
    }
}
