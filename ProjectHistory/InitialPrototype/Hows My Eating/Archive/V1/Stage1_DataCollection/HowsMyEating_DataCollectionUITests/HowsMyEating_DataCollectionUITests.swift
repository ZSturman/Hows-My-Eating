//
//  HowsMyEating_DataCollectionUITests.swift
//  HowsMyEating_DataCollectionUITests
//
//  Created by Zachary Sturman on 8/14/24.
//  Updated on 2025-02-20
//

import XCTest

final class HowsMyEating_DataCollectionUITests: XCTestCase {
    
    private var app: XCUIApplication!
    
    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launch()
    }
    
    override func tearDownWithError() throws {
        // Terminate the app after each test to help ensure a clean state.
        app.terminate()
        app = nil
    }

    @MainActor
    func testExample() throws {
        // Use the already launched app instance.
        XCTAssertTrue(app.wait(for: .runningForeground, timeout: 5), "App did not launch into foreground")
    }

    @MainActor
    func testLaunchPerformance() throws {
        if #available(iOS 13.0, *) {
            let options = XCTMeasureOptions()
            options.iterationCount = 5
            measure(metrics: [XCTApplicationLaunchMetric()], options: options) {
                // Each measurement launches a new instance.
                let newApp = XCUIApplication()
                newApp.launch()
            }
        }
    }
    
    func testRecordNewDataNavigation() {
        let recordButton = app.buttons["Record New Data"]
        XCTAssertTrue(recordButton.waitForExistence(timeout: 5), "Record New Data button did not appear")
        recordButton.tap()
        
        let setReferenceButton = app.buttons["Set Reference Frame"]
        XCTAssertTrue(setReferenceButton.waitForExistence(timeout: 5), "Set Reference Frame button did not appear")
    }
    
    func testStartStopRecording() {
        let recordButton = app.buttons["Record New Data"]
        XCTAssertTrue(recordButton.waitForExistence(timeout: 5), "Record New Data button did not appear")
        recordButton.tap()
        
        let startRecording = app.buttons["Start Recording"]
        XCTAssertTrue(startRecording.waitForExistence(timeout: 5), "Start Recording button did not appear")
        startRecording.tap()
        
        // Use an expectation to wait for the Stop Recording button to appear
        let stopButton = app.buttons["Stop Recording"]
        let existsPredicate = NSPredicate(format: "exists == true")
        expectation(for: existsPredicate, evaluatedWith: stopButton, handler: nil)
        waitForExpectations(timeout: 5)
        
        XCTAssertTrue(stopButton.exists, "Stop Recording button did not appear after starting")
        stopButton.tap()
    }
    
    func testShareSheetPresentation() {
        let shareButton = app.buttons["Share"]
        XCTAssertTrue(shareButton.waitForExistence(timeout: 5), "Share button did not appear")
        shareButton.tap()
        
        // Wait for the share sheet (ActivityContentView) to appear
        let shareSheetExpectation = XCTNSPredicateExpectation(predicate: NSPredicate(format: "exists == true"), object: app.otherElements["ActivityContentView"])
        XCTAssertEqual(XCTWaiter.wait(for: [shareSheetExpectation], timeout: 5), .completed, "Share sheet did not appear")
        
        let cancelButton = app.buttons["Cancel"]
        XCTAssertTrue(cancelButton.waitForExistence(timeout: 5), "Cancel button did not appear in share sheet")
        cancelButton.tap()
    }
    
    func testFolderDeletionConfirmation() {
        let firstFolderCell = app.tables.cells.element(boundBy: 0)
        XCTAssertTrue(firstFolderCell.waitForExistence(timeout: 5), "Folder cell did not appear")
        print(app.debugDescription)  // Useful for debugging the UI structure
        
        // Swipe to reveal the delete button and tap it.
        firstFolderCell.swipeLeft()
        let deleteButton = firstFolderCell.buttons["Delete"]
        XCTAssertTrue(deleteButton.waitForExistence(timeout: 5), "Delete button did not appear after swipe")
        deleteButton.tap()
        
        // Verify that an alert appears asking for confirmation.
        let alert = app.alerts.element
        XCTAssertTrue(alert.waitForExistence(timeout: 5), "Deletion confirmation alert did not appear")
        
        // Dismiss the alert by tapping the 'Cancel' button.
        let cancelButton = alert.buttons["Cancel"]
        XCTAssertTrue(cancelButton.waitForExistence(timeout: 5), "Cancel button did not appear in deletion alert")
        cancelButton.tap()
    }
    
    func testFolderSelectionHighlight() {
        let firstFolderCell = app.tables.cells.element(boundBy: 0)
        XCTAssertTrue(firstFolderCell.waitForExistence(timeout: 5), "Folder cell did not appear")
        print(app.debugDescription)  // Useful for debugging the UI structure
        
        // Tap the first folder cell.
        firstFolderCell.tap()
        
        // Wait for the checkmark image to appear in the cell.
        let checkmark = firstFolderCell.images["checkmark"]
        XCTAssertTrue(checkmark.waitForExistence(timeout: 5), "Checkmark did not appear after folder selection")
    }
}
