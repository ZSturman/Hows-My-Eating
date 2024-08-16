# How's My Eating? Data Collection

## Overview

**How's My Eating? Data Collection** is an iOS application designed to help users monitor and analyze their eating habits by capturing motion data from AirPods and recording videos of their eating sessions. The app collects and stores motion data alongside the recorded video, allowing users to review their eating patterns and receive real-time feedback on their eating pace.

## Features

- **Motion Data Collection**: Captures motion data from AirPods, including attitude, rotation rate, user acceleration, and gravity, to analyze eating habits.
- **Video Recording**: Records video of the eating session using the device’s camera, synchronized with the collected motion data.
- **Data Storage**: Saves motion data and video files within the app's document directory, ensuring data persistence across app sessions.
- **Export Functionality**: Allows users to export recorded data (motion data and videos) as a ZIP file for further analysis or sharing.
- **Real-Time Feedback**: Displays motion data status in real-time during recording to inform users if motion data is being correctly captured.

## Technologies Used

- **SwiftUI**: For building the user interface.
- **AVFoundation**: For managing video recording and playback.
- **Core Motion**: For collecting motion data from connected AirPods.
- **SwiftData**: For managing data persistence within the app.
- **FileManager**: For handling file operations such as saving, copying, and exporting data.
- **PHPhotoLibrary**: For handling media authorization and potential future expansion to save files in the photo library.

## Installation

To run this app, you'll need a Mac with Xcode installed. Follow these steps:

1. **Clone the repository**:

   ```bash
   git clone https://github.com/ZSturman/Hows-My-Eating.git
   ```

2. **Open the project in Xcode**:

   ```bash
   cd Stage1_DataCollection
   open HowsMyEating_DataCollection.xcodeproj
   ```

3. **Build and run the project**:
   - Select your target device (an iOS device with iOS 14.0 or later).
   - Click the **Run** button or press `Cmd + R`.

## Usage

1. **Record New Data**:
   - On the main screen, tap "Record New Data" to start recording a new session.
   - The app will begin capturing motion data and recording video simultaneously.
   - Tap "Stop Recording" when you are done.

2. **View Recorded Data**:
   - View a list of recorded sessions on the main screen.
   - Tap on a session to see details, including the number of motion data samples collected and the path to the recorded video.

3. **Playback Recorded Video**:
   - From the session details screen, tap "Play Video" to watch the recorded video.

4. **Export Data**:
   - On the main screen, tap "Export All Data" to export all recorded sessions as a ZIP file.
   - Share the exported ZIP file using the iOS share sheet.

## Data Management

The app saves motion data and videos in the app's document directory, ensuring that the data persists across app sessions. It also checks for the existence of files before playback or export to ensure data integrity.

### File Structure

- **Motion Data**: Saved as JSON files.
- **Videos**: Saved in the `.mov` format.
- **Export**: Both JSON files and videos are exported together in a ZIP file.

## Known Issues

- **File Persistence in Development Mode**: During development, the app's sandbox environment may change, causing issues with file paths. This is not expected to affect the app in a production environment.

- **Motion Data Availability**: If motion data is not available, the app will notify the user during the recording session.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes. Make sure to include a detailed description of the changes you’ve made.

