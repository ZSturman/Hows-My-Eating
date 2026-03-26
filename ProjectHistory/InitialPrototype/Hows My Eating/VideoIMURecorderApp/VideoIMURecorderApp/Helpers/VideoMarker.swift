//
//  VideoMarker.swift
//  VideoIMURecorderApp
//
//  Created by Zachary Sturman on 11/13/25.
//

import Foundation
import SwiftUI

struct VideoMarker: Identifiable, Hashable {
    let id: UUID
    var time: Double  
    var kind: MarkerKind
}
