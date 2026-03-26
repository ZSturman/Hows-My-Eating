//
//  Segment.swift
//  VideoIMURecorderApp
//
//  Created by Zachary Sturman on 11/13/25.
//


import Foundation
import SwiftUI

struct Segment: Identifiable, Hashable {
    let id = UUID()
    var startTime: Double
    var endTime: Double
    var isChewing: Bool
}
