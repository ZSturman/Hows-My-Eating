# How’s My Eating? - Labelling

## Overview

**How’s My Eating? - Labelling** is a Rust application with a React front end, designed to help users label and manage video files alongside associated motion data. This application is part of the broader “How’s My Eating?” project, which aims to develop healthier eating habits by providing real-time feedback based on motion data.

## Features

- **File Import and Management:** Allows users to import video files for labeling. Supports multiple video formats, including .mp4, .avi, .mov, .wmv, and .mkv.
- **Video Playback**: Integrated video player for reviewing and labeling imported video files. Features include play/pause, fast forward, rewind, and timeline navigation.
- **Data Synchronization**: Ensures that motion data files are synchronized with video playback for accurate labeling.
- **Labeling Interface**: Users can add labels to specific segments of the video, helping to create a comprehensive dataset for further analysis.

## Technologies Used

- **Rust**: Backend logic and file management.
- **React**: Front-end interface for user interaction and video playback.
- **Tauri**: Framework used for building the desktop application.
- **Tailwind CSS**: Utility-first CSS framework used for styling the application.
- **ReactPlayer**: For embedding and controlling video playback within the React application.
- **@tauri-apps/api**: For interacting with the file system and handling dialog operations in the Tauri application.

## Installation

To run this application, follow these steps:

1. **Clone the repository**:

    ```bash
    git clone https://github.com/ZSturman/Hows-My-Eating.git
    ```

2. **Navigate to the Stage2 directory**:

    ```bash
    cd Stage2_Labelling
    ```

3. **Install dependencies**:

    ```bash
    npm install
    ```

4. **Run the development server**:

    ```bash
    npm run tauri dev
    ```

5. **Build the application**:

    ```bash
    npm run tauri build
    ```

## Usage

1. **Import Video Files**:
    - Click the “Select Input File” button to open a file dialog and choose video files from your system. The selected files will be imported into the application.

2. **Review and Label**:
    - Use the integrated video player to review the imported videos. You can pause, fast forward, or rewind the video to specific points for precise labeling.

3. **Add Labels**:
    - Label specific segments of the video directly within the application. These labels will be stored and synchronized with the motion data for later analysis.

4. **Export Labeled Data**:
    - Once labeling is complete, the labeled video and motion data can be exported for use in the How’s My Eating? project or further analysis.

## File Structure

- **Motion Data**: Motion data files are stored in JSON format.
- **Imported Files**: Imported video files are listed and managed within the application.
- **Labels**: Labels added during video playback are stored alongside the video files.

## Known Issues

- **File Compatibility**: Some video formats may not be fully supported by the application. Ensure that the imported files are in a compatible format for seamless playback and labeling.

## Contributing

Contributions to the project are welcome. Please fork the repository, create a new branch for your changes, and submit a pull request with a detailed description of the updates.
