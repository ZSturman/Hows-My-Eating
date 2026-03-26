//
//  HowsMyEating_DataCollectionUITestsLaunchTests.swift
//  HowsMyEating_DataCollectionUITests
//
//  Created by Zachary Sturman on 8/14/24.
//  Updated on 2025-02-20
//

import XCTest

final class HowsMyEating_DataCollectionUITestsLaunchTests: XCTestCase {

    override class var runsForEachTargetApplicationUIConfiguration: Bool {
        true
    }

    override func setUpWithError() throws {
        continueAfterFailure = false
    }

    @MainActor
    func testLaunch() throws {
        let app = XCUIApplication()
        app.launch()

        // Additional steps after app launch can be added here.
        let attachment = XCTAttachment(screenshot: app.screenshot())
        attachment.name = "Launch Screen"
        attachment.lifetime = .keepAlways
        add(attachment)
    }
}
