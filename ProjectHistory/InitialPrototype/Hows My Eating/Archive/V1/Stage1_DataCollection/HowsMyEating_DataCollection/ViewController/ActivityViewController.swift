//
//  ActivityViewController.swift
//  HowsMyEating_DataCollection
//
//  Created by Zachary Sturman on 8/25/24.
//

import Foundation
import SwiftUI
import UIKit

struct ActivityViewController: UIViewControllerRepresentable {
    var folderURL: URL
    var completion: (() -> Void)?

    func makeUIViewController(context: Context) -> UIActivityViewController {
        let activityVC = UIActivityViewController(activityItems: [folderURL], applicationActivities: nil)
        activityVC.completionWithItemsHandler = { (activityType, completed, returnedItems, activityError) in
            if completed {
                self.completion?()
            }
        }
        return activityVC
    }

    func updateUIViewController(_ uiViewController: UIActivityViewController, context: Context) {
        // Nothing to update here
    }
}
