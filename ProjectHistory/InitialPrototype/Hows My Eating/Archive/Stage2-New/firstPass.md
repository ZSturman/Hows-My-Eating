# Setup

## Open App

1. Get the Project json file

    ``` ts
    const projectJson: ProjectJson = await checkProjectJson()
    ```

2. Get the directory to use for importing data OR select specific data directories

3. Import data

    ``` ts

    const projectDataJsons: ProjectDataJsons = []

    function importData(dataDirectory) {
        // for each data directory
        const validatedData: { validated: boolean, jsonFiles: string[], movFiles: string[], audioFiles: string[], csvFiles: string[], otherFiles: string[], directories: string[] } = await doesTheDirectoryContainMovAndJsonFile()

        if (!validateData.validated) {
            // skip this one and add it to the logger saying it's incorrect
            return 
        } 

        // copy the data into the appDataDir

        const { motionData, movData, otherData } = await checkDataTypes(validatedData)  

        const dataSync = await checkIfDataIsSynced(motionData, movData)

        // dataSync > 0 then motion data is ${dataSync} ms shorter than mov
        // dataSync < 0 then motion data is ${dataSync} ms longer than mov
        // dataSync === 0 then motion data and mov are teh same amount of time

       const projectDataJson =  await createProjectDataJson(someData, dataSync, files, andStuff)
       projectDataJsons.push(projectDataJson)
    }

    await updateProjectJson(projectDataJsons) // this just keeps a record of when the app data is updated and where all the files are and stuff, not all the details from the projectDataJsons

   

    ```

4. Open data in UI

    ``` ts

    const dataSync = await checkIfDataIsSynced(motionData, movData)
    const unacceptableOffset = 50
    while (abs(dataSync) > unacceptableOffset) {
            await manuallySyncData() // To be created later. This will involve probably trimming the mov at the beginning or the end.
            // Also there will be an algorithm the find the largest changes in either userAcceleration or rotationRate to be used as the marker to manually sync
    }

    const audioFile = await getAudioFile(movData)

    const csvs = await createCsvFiles(motionData, numebrOfFrames, movLength)
    const projectDataJson = await updateProjectDataJson(csvs)
    await updateProjectJson(projectDataJson) 

    ```

5. Labelling data

    ``` ts

    // double check data incase something has changed since the last time or something
    const dataSync = await checkIfDataIsSynced(motionData, movData)

    let totalNumberOfFrames: number = projectDataJson.numberOfFrames
    let labelledFrames: LabbelledFrame[] = [] 
    let unlabelledFrames: UnlabbelledFrame[] = []

    const csvExists = await checkForCsv()

    if (csvExists) {
        // go through and find the rows that have been labelled
        if (hasBeenLabelled) {
            // turn rown to LabbelledFrame and push to labelledFrames
        } else {
            // turn rown to UnlabbelledFrame and push to unlabelledFrames
        }
    } else {
        const frames: Frame[] = await convertMovToFrames(mov) // This makes each frame of the mov (recoreded at 30fps, maybe add a check to make sure it is really 30fps) a Frame type. 
        unlabelledFrames.push(frames)
    }

    const frames = // unlabelledFrames & labelledFrames combined and sorted by frameIndex

    await updateProjectDataJson(frames)

    // frames is passed to the TimeLine component. 

    // the labelling process is handled by playing the video and when a button or key is clicked the current frame is received and that key press updates the state of that frame

    // add some time buffer or before the window or screen is left or before the app is closed to write that updated data to the csv and the project data.

    // If all frames have been labelled update the projectJson to show that it's been labelled.
  
    ```

6. Export data

    ``` typescript

    await checkThatLabelsHaveBeenAdded()
    await saveTheCSVFileSomewhere()
    // update the projectDataJson to show that it's been exported
    // updateProjectJson to show that it's been exported

    ```

## Functions

``` ts

async function checkProjectJson(appDataDirectoryPath: string?, customProjectJsonFilename: string?): Promise<{messages: Logger[], projectJson: ProjectJson}> {
    let appDataDir
    if (appDataDirectoryPath) {
        const appDataDirectory = await exists(appDataDirectory)
        if (no permission) {
            "Cannot access custom directory path. Defaulting to App Data Directory" 
             appDataDir = await appDataDir()
        } else if (doesnt exist) {
            "Path does not exist. Defaulting to App Data Directory"
            appDataDir = await appDataDir()
        } else {
            appDataDir = appDataDirectoryPath
        }
    } else {
        appDataDir = await appDataDir()
    }

    const projectJsonFilename = customProjectJsonFilename ? customProjectJsonFilename : "HowsMyEatingProjectJson"
    const filePath = appDataDir + projectJsonFilename + ".json"
    const projectJsonFile = await exists(filePath)
    if (doesnt exist) {
        `Custom Json file does not exist. Creating new file: ${projectJsonFilename}`
        const defaultProjectJson: ProjectJson = {
            /// 
        }
        await createProjectJson(defaultProjectJson, projectJsonFilename)
        return defaultProjectJson
    } else {
        const jsonFileContent = await readFile(projectJsonFile)
        const projectJson:ProjectJson = await JSON(jsonFileContent)

        // TYPE GUARD HERE
        
        return projectJson
    }
}

async function checkDataTypes(validatedData) {
     // check that there is a json file and a mov file and that they match the name of the directory they are in. 
        if ( json does not match dir name) {
            if ( validateData.jsonFiles.length > 1 ) {
                // ask the user which file contains the motion data
            } else {
                // have user confirm that the json file in the directory is the correct one
            }
        }

        if ( mov does not match dir name) {
            if ( validateData.movFiles.length > 1 ) {
                // ask the user which file contains the recorded data
            } else {
                // have user confirm that the mov file in the directory is the correct one
            }
        }

        // ask about the nested directories

        // ask about csvs 

        // ask about other files

}

async function checkIfDataIsSynced(motionData, movData): number {
    // using the length of the mov and the timestamps from motionData check that the time lines up.
    // return the amount of offset and also log it out
}

async function createCsvFiles(motionData, numebrOfFrames, movLength): CSVData[] {
    // for each motionData timestamp create a row in the csv file.
    
    const headers = {
        timestamp: "TIMESTAMP",
        // motion data parameters
        // frame of the mov that corresponds to that timestamp
        isEating: "EATING",
        mouthState: "MOUTHSTATE",
        labels: "LABELS",
    }
    

}



```

## Types

``` ts

// corresponding to the app as a whole
type ProjectJson = {
}

// data corresponding to the specific data files 
type ProjectDataJson = {
}

type Logger = {
    title: string
    description: string
    type: "INFO" | "ERROR" | "WARNING" | "SUCCESS"
    timestamp: number
    forUi: boolean
}

type UnlabbelledFrame = {
    index: number
    movFilePath: string
    movTimestamp: number
}

type LabelledFrame = UnlabbelledFrame & {
    isEating: boolean
    mouthState: string
    labels: string[]
}

```
