//
//  ContentView.swift
//  HowsMyEating_DataCollection
//
//  Created by Zachary Sturman on 8/14/24.
//

import SwiftUI
import SwiftData

struct ContentView: View {
    @Environment(\.modelContext) private var modelContext
    @Query var recordedDataList: [CapturedMotionAndMovieData]

    var body: some View {
        NavigationView {
            VStack {
                NavigationLink(destination: CameraControlView()) {
                    Text("Record Data")
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
                                Text("Data: \(recordedData.motionArray.count)")
                                    .padding()
                                    .background(Color.green)
                                    .foregroundColor(.white)
                                    .cornerRadius(8)
                            }
                            .padding()
                        }
                            
                    }
                    
                    
                    

                }
            }
            .navigationTitle("Measured Munch Collector")
            
        }
    }



    private func deleteItems(offsets: IndexSet) {
        withAnimation {
            for index in offsets {
                modelContext.delete(recordedDataList[index])
            }
        }
    }
}


//
//#Preview {
//    ContentView()
//        .modelContainer(for: Item.self, inMemory: true)
//}


