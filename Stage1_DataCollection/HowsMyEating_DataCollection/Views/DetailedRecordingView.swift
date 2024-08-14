//
//  DetailedRecordingView.swift
//  HowsMyEating_DataCollection
//
//  Created by Zachary Sturman on 8/14/24.
//

import Foundation
import SwiftUI
import SwiftData


struct DetailedRecordingView: View {

    @Environment(\.modelContext) private var modelContext
    var recordedData: CapturedMotionAndMovieData
    
    @State var isShowingDetailedView: Bool = false
    
    var body: some View {
        VStack {
            Text("Motion Data")
            
            if isShowingDetailedView {
          
                    Text("\(recordedData.motionArray.count)")
                Text("\(recordedData.moviePath)")
                }
            }
            

            
        }
    }

