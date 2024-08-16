////
////  MediaLibrary.swift
////  HowsMyEating_DataCollection
////
////  Created by Zachary Sturman on 8/15/24.
////
//
//import Foundation
//import Photos
//import UIKit
//
///// An object that writes photos and movies to the user's Photos library.
//actor MediaLibrary {
//    
//    // Errors that media library can throw.
//    enum Error: Swift.Error {
//        case unauthorized
//        case saveFailed
//    }
//    
//    
//    // MARK: - Authorization
//    
//    private var isAuthorized: Bool {
//        get async {
//            let status = PHPhotoLibrary.authorizationStatus(for: .addOnly)
//            /// Determine whether the user has previously authorized `PHPhotoLibrary` access.
//            var isAuthorized = status == .authorized
//            // If the system hasn't determined the user's authorization status,
//            // explicitly prompt them for approval.
//            if status == .notDetermined {
//                // Request authorization to add media to the library.
//                let status = await PHPhotoLibrary.requestAuthorization(for: .addOnly)
//                isAuthorized = status == .authorized
//            }
//            return isAuthorized
//        }
//    }
//
//    // MARK: - Saving media
//    /// Saves a movie to the app's data directory and returns the file URL.
//    func save(movie: Movie) async throws -> URL {
//        do {
//            let fileManager = FileManager.default
//            let documentsDirectory = fileManager.urls(for: .documentDirectory, in: .userDomainMask).first!
//            let movieURL = documentsDirectory.appendingPathComponent(movie.url.lastPathComponent)
//            
//            // Move the movie file to the documents directory
//            try fileManager.moveItem(at: movie.url, to: movieURL)
//            
//            
//            return movieURL
//        } catch {
//            throw Error.saveFailed
//        }
//    }
//    
//    
//    // MARK: - Location management
//    
//    private let locationManager = CLLocationManager()
//    
//    private var currentLocation: CLLocation? {
//        get async throws {
//            if locationManager.authorizationStatus == .notDetermined {
//                locationManager.requestWhenInUseAuthorization()
//            }
//            // Return the location for the first update.
//            return try await CLLocationUpdate.liveUpdates().first(where: { _ in true })?.location
//        }
//    }
//}
//
