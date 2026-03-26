//
//  RoutePickerView.swift
//  VideoIMURecorderApp
//
//  Created by Assistant on 11/12/25.
//

import SwiftUI
import AVKit

struct RoutePickerView: UIViewRepresentable {
    func makeUIView(context: Context) -> AVRoutePickerView {
        let v = AVRoutePickerView()
        v.prioritizesVideoDevices = false
        if #available(iOS 13.0, *) {
            v.activeTintColor = .systemBlue
        }
        v.tintColor = .white
        return v
    }

    func updateUIView(_ uiView: AVRoutePickerView, context: Context) {
        // No dynamic updates needed
    }
}
