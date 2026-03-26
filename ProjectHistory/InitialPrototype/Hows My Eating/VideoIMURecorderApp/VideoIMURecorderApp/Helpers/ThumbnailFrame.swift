//
//  ThumbnailFrame.swift
//  VideoIMURecorderApp
//
//  Created by Zachary Sturman on 11/13/25.
//


import Foundation
import SwiftUI
import AVKit

struct ThumbnailFrame: Identifiable {
    let id: Int
    let time: CMTime
    let image: UIImage?
}
