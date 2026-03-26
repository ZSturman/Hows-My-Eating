# Hows My Eating - Stage 2: Labelling

## 1. Open App

### Step 1: Get the Project JSON File

``` ts
const projectJson: ProjectJson = await checkProjectJson();
```

### Step 2: Get the Directory for Importing Data

- Select the directory to use for importing data, or select specific data directories.

### Step 3: Import Data

    ```typescript

    const projectDataJsons: ProjectDataJson[] = [];

    async function importData(dataDirectory: string) {
        // Validate data directory
        const validatedData = await doesTheDirectoryContainMovAndJsonFile(dataDirectory);

        if (!validatedData.validated) {
            // Log invalid directory and skip processing
            return;
        }

        // Process and copy the data into the appDataDir
        const { motionData, movData, otherData } = await checkDataTypes(validatedData);

        // Check if data is synced
        const dataSync = await checkIfDataIsSynced(motionData, movData);

        // Create a ProjectDataJson entry
        const projectDataJson = await createProjectDataJson(motionData, dataSync, movData, otherData);
        projectDataJsons.push(projectDataJson);
    }

    // Update project JSON with imported data
    await updateProjectJson(projectDataJsons);

    ```

### Step 4. Open Data in UI

    ``` ts

    const dataSync = await checkIfDataIsSynced(motionData, movData);
    const unacceptableOffset = 50;

    // If data offset is greater than the acceptable limit, manually sync the data
    while (Math.abs(dataSync) > unacceptableOffset) {
        await manuallySyncData(); // Placeholder: Implement manual sync logic
    }

    const audioFile = await getAudioFile(movData);
    const csvs = await createCsvFiles(motionData, numberOfFrames, movLength);

    // Update project data with CSVs
    const projectDataJson = await updateProjectDataJson(csvs);
    await updateProjectJson(projectDataJson);

    ```

### Step 5. Labelling Data

    ``` ts

    // Re-check if data is still synced
    const dataSync = await checkIfDataIsSynced(motionData, movData);

    let totalNumberOfFrames: number = projectDataJson.numberOfFrames;
    let labelledFrames: LabelledFrame[] = [];
    let unlabelledFrames: UnlabelledFrame[] = [];

    const csvExists = await checkForCsv();

    if (csvExists) {
        // Load frames from CSV
        if (hasBeenLabelled) {
            // Convert rows to LabelledFrame and push to labelledFrames
        } else {
            // Convert rows to UnlabelledFrame and push to unlabelledFrames
        }
    } else {
        // Convert video to frames if no CSV exists
        const frames: Frame[] = await convertMovToFrames(mov);
        unlabelledFrames.push(...frames);
    }

    const frames = [...unlabelledFrames, ...labelledFrames].sort((a, b) => a.index - b.index);
    await updateProjectDataJson(frames);

    // Handle the labeling process in the TimeLine component
    // Add buffer time to save data before closing the app

    // Update projectJson to indicate labeling is complete if all frames are labeled
  
    ```

### Step 6. Export data

    ``` typescript
    await checkThatLabelsHaveBeenAdded();
    await saveTheCSVFileSomewhere();

    // Update projectDataJson and projectJson to show that data has been exported
    ```

## 2. Functions

### Function: checkProjectJson

    ``` ts
    async function checkProjectJson(appDataDirectoryPath?: string, customProjectJsonFilename?: string): Promise<{ messages: Logger[], projectJson: ProjectJson }> {
        let appDataDir;
        if (appDataDirectoryPath) {
            const appDataDirectory = await exists(appDataDirectoryPath);
            if (!appDataDirectory || noPermission) {
                console.warn("Cannot access custom directory path. Defaulting to App Data Directory");
                appDataDir = await appDataDir();
            } else {
                appDataDir = appDataDirectoryPath;
            }
        } else {
            appDataDir = await appDataDir();
        }

        const projectJsonFilename = customProjectJsonFilename || "HowsMyEatingProjectJson";
        const filePath = `${appDataDir}/${projectJsonFilename}.json`;
        const projectJsonFile = await exists(filePath);

        if (!projectJsonFile) {
            console.info(`Custom Json file does not exist. Creating new file: ${projectJsonFilename}`);
            const defaultProjectJson: ProjectJson = {}; // Define default JSON structure
            await createProjectJson(defaultProjectJson, projectJsonFilename);
            return { messages: [], projectJson: defaultProjectJson };
        } else {
            const jsonFileContent = await readFile(projectJsonFile);
            const projectJson: ProjectJson = JSON.parse(jsonFileContent);
            return { messages: [], projectJson };
        }
    }
    ```

### Function: checkDataTypes

    ``` ts 
    async function checkDataTypes(validatedData): Promise<{ motionData: any, movData: any, otherData: any }> {
        // Check if JSON and MOV files match directory names
        if (jsonDoesNotMatchDirName(validatedData)) {
            if (validatedData.jsonFiles.length > 1) {
                // Prompt user to select the correct JSON file
            } else {
                // Confirm with user if the JSON file is correct
            }
        }

        if (movDoesNotMatchDirName(validatedData)) {
            if (validatedData.movFiles.length > 1) {
                // Prompt user to select the correct MOV file
            } else {
                // Confirm with user if the MOV file is correct
            }
        }

        // Handle other file types and directories
        return { motionData: null, movData: null, otherData: null }; // Placeholder return
    }
    ```

### Function: checkIfDataIsSynced

    ``` ts
    async function checkIfDataIsSynced(motionData, movData): Promise<number> {
        // Compare MOV length and motionData timestamps to determine offset
        // Return the time offset and log the result
        return 0; // Placeholder return
    }
    ```

### Function: createCsvFiles

    ``` ts
    async function createCsvFiles(motionData, numberOfFrames, movLength): Promise<CSVData[]> {
        // Create CSV rows for each motionData timestamp
        const headers = {
            timestamp: "TIMESTAMP",
            isEating: "EATING",
            mouthState: "MOUTHSTATE",
            labels: "LABELS",
        };

        // Generate and return CSV data
        return [];
    }
    ```

## 3. Types

### Types Definitions

    ``` ts
    // Main project configuration type
    type ProjectJson = {
        projectName: string; // Name of the project
        createdDate: string; // Date of project creation
        modifiedDate: string; // Date of last modification
        dataDirectories: {
            exportStatus: boolean; // Flag indicating if the data has been exported
            projectDataJson: string; // path indicating where to find the json file
            isLabelingComplete: boolean; // Flag indicating if all frames have been labeled
            motionDataFilePath: string; // Path to the motion data file
            movDataFilePath: string; // Path to the MOV file
            audioFile?: string // Path to Audio file
            isDataSynced: boolean; // Flag indicating if data is synchronized
            csvFilePath?: string; // Path to the CSV file, if it exists
        }
        
        
       
    };

    // Type representing specific data files and their associated metadata
    type ProjectDataJson = {
        dataDirectory: string; // Directory where the data is stored
        motionDataFilePath: string; // Path to the motion data file
        movDataFilePath: string; // Path to the MOV file
        audioFile: string // Path to Audio file
        otherFilePaths: string[]; // Paths to other associated data files
        isDataSynced: boolean; // Flag indicating if data is synchronized
        numberOfFrames: number; // Total number of frames
        labeledFramesCount: number; // Number of labeled frames
        unlabelledFramesCount: number; // Number of unlabelled frames
        csvFilePath?: string; // Path to the CSV file, if it exists
        hasBeenLabelled: boolean; // Flag indicating if the data has been labeled
    };

    type MouthState = "OPEN" | "CLOSED" | "OPENING" | "CLOSING"

    type PrimaryBodyState = "SITTING" | "STANDING" | "WALKING" 

    type SecondaryBodyState = "LEAN_FORWARD" | "LEAN_BACKWARD" | "LEAN_LEFT" | "LEAN_RIGHT" 

    type Labels = {
        isEating: boolean 
        mouthState: MouthState // State of the mouth
        primaryBodyState: PrimaryBodyState // The action associated with the whole video. This should change in frequently.
        secondaryBodyState: SecondaryBodyState // Action that changes from time to time such as leaning forward to take another bite
        isTalking: boolean 
        otherLabels: string[] // List of other labels 
    }


    // Type for frames that have not been labeled yet
    type Frame = {
        index: number; // Frame index
        timestamp: number; // Timestamp in the MOV file
        labels: Labels
        labelled: boolean; // Whether the frame has been labelled

    };



    // Type for CSV data entries generated from motion data
    type CSVData = {
        filePath: string
        movPath: string
        motionDataPath: string
        rows: CsvRow[]
    };

    // Type for CSV row data entries with flattened structure
    type CsvRow = {
        // General information
        timestamp: number; // Timestamp of the data

        // Frame data
        frameIndex: number; // Frame index
        frameTimestamp: number; // Timestamp in the MOV file
        isLabelled: boolean; // Whether the frame has been labeled

        // Labels
        isEating: boolean; // Indicates if eating is detected
        mouthState: MouthState; // State of the mouth (e.g., OPEN, CLOSED)
        primaryBodyState: PrimaryBodyState; // Primary body state (e.g., SITTING, STANDING)
        secondaryBodyState: SecondaryBodyState; // Secondary body state (e.g., LEAN_FORWARD)
        isTalking: boolean; // Indicates if the person is talking
        otherLabels: string[]; // Other labels associated with the frame

        // Motion Data
        gravityX: number; // Gravity vector component in the x direction
        gravityY: number; // Gravity vector component in the y direction
        gravityZ: number; // Gravity vector component in the z direction
        transformedRotationX: number; // Transformed rotation quaternion component in the x direction
        transformedRotationY: number; // Transformed rotation quaternion component in the y direction
        transformedRotationZ: number; // Transformed rotation quaternion component in the z direction
        transformedRotationW: number; // Transformed rotation quaternion scalar component
        rotationRateX: number; // Rotation rate around the x axis
        rotationRateY: number; // Rotation rate around the y axis
        rotationRateZ: number; // Rotation rate around the z axis
        userAccelerationX: number; // User acceleration component in the x direction
        userAccelerationY: number; // User acceleration component in the y direction
        userAccelerationZ: number; // User acceleration component in the z direction
        attitudeRoll: number; // Roll angle in radians
        attitudePitch: number; // Pitch angle in radians
        attitudeYaw: number; // Yaw angle in radians
    };

    // Additional utility types for functions and data management

    // Represents motion data captured from sensors at a specific timestamp
    type MotionData = {
        timestamp: number; // The timestamp of the data sample
        gravity: {
            x: number; // Gravity vector component in the x direction
            y: number; // Gravity vector component in the y direction
            z: number; // Gravity vector component in the z direction
        };
        transformedRotation: {
            x: number; // Transformed rotation quaternion component in the x direction
            y: number; // Transformed rotation quaternion component in the y direction
            z: number; // Transformed rotation quaternion component in the z direction
            w: number; // Transformed rotation quaternion scalar component
        };
        rotationRate: {
            x: number; // Rotation rate around the x axis
            y: number; // Rotation rate around the y axis
            z: number; // Rotation rate around the z axis
        };
        userAcceleration: {
            x: number; // User acceleration component in the x direction
            y: number; // User acceleration component in the y direction
            z: number; // User acceleration component in the z direction
        };
        attitude: {
            roll: number; // Roll angle in radians
            pitch: number; // Pitch angle in radians
            yaw: number; // Yaw angle in radians
        };
    };

    type MovData = {
        filePath: string; // Path to the MOV file
        length: number; // Length of the MOV file in seconds
        fps: number; // Frames per second
        numberOfFrames: number
    };

    type OtherData = {
        filePaths: string[]; // Paths to additional files related to the project
    };

    // Type for logger entries used in the application
    type Logger = {
        title: string;
        description: string;
        type: "INFO" | "ERROR" | "WARNING" | "SUCCESS";
        timestamp: number; // Unix timestamp for the log entry
        forUi: boolean; // Indicates if the log is intended for UI display
    };
    ```
