//
//  HowsMyEating_DataCollectionApp.swift
//  HowsMyEating_DataCollection
//
//  Created by Zachary Sturman on 8/14/24.
//

import SwiftUI
import SwiftData

@main
struct HowsMyEating_DataCollectionApp: App {
    var sharedModelContainer: ModelContainer = {
        let schema = Schema([
            CapturedMotionAndMovieData.self,
        ])
        let modelConfiguration = ModelConfiguration(schema: schema, isStoredInMemoryOnly: false)

        do {
            return try ModelContainer(for: schema, configurations: [modelConfiguration])
        } catch {
            fatalError("Could not create ModelContainer: \(error)")
        }
    }()

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .modelContainer(sharedModelContainer)
    }
}
