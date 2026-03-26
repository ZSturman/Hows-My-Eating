//
//  MarkerKind.swift
//  VideoIMURecorderApp
//
//  Created by Zachary Sturman on 11/13/25.
//



enum MarkerKind: String, Codable {
    case startChewing
    case stopChewing
}

enum ChewingState {
    case chewing
    case notChewing
}
