//
//  CSVRow.swift
//  VideoIMURecorderApp
//
//  Created by Zachary Sturman on 11/12/25.
//

import Foundation

    struct CSVRow: Identifiable {
        let id = UUID()
        let timestamp: Double
        var fieldsWithoutLabel: [String]
        var label: Bool?
    }

    struct LabelMarker: Identifiable {
        let id = UUID()
        var time: Double
        var labelForNext: Bool
    }
