import { exists, readTextFile, readDir } from "@tauri-apps/plugin-fs";
import { join } from "@tauri-apps/api/path";
import { isDirectory } from "../utilities/directoryChecks";
import { csvFileHasContent, jsonFileHasContent } from "../utilities/fileChecks";
import { runCollectMovInfo } from "./commands/collectMovInfo";
import { runProcessVisuals } from "./commands/processVisuals";
import { runComputeRatios } from "./commands/computeRatios";
import { runMergeLabels } from "./commands/merge";
import { runGetChunks } from "./commands/chunks";
import { createVerifiedJson } from "../utilities/createVerifiedJson";
import { VideoChunkStatus } from "@/types/Markers";

export async function processTaskPipeline(
  dataPath: string,
  appConfig: AppConfig
): Promise<"enqueued" | "completed" | "waiting" | "errored" | "processing"> {
  // Initialize appConfig variables
  const outputProcessedVideo = appConfig.outputProcessedVideo || true;
  const labelledJsonStartsWithString: string =
    appConfig.labelledJsonStartsWithString || "labelled";
  const importedDataParentFolderName: string =
    appConfig.importedDataParentFolderName || "imported";
  const mergedCsvFileName: string = appConfig.mergedCsvFileName || "merged";
  const chunksDirectoryName: string = appConfig.chunksDirectoryName || "chunks";
  const verifiedJsonStartsWithString: string =
    appConfig.verifiedJsonStartsWithString || "verified";
    const movInfoFileName: string = appConfig.movInfoFileName || "mov_info";
    const processVisualsCsvFileName: string = appConfig.processVisualsCsvFileName || "process-visuals";
    const compareVisualsCsvFileName: string = appConfig.compareVisualsCsvFileName || "compare-visuals";

  // Initialize variables
  let importedFolderName: string;
  let motionDataJsonFilePath: string;
  let originalImportedVideoFilePath: string;
  let movInfoFilePath: string;
  let mainThumbnailPath: string | null = null;
  let scrubbingThumbnailsPaths: string[] = [];
  let pointsDataFilePath: string;
  let processedVideoFilePath: string | null = null;
  let ratiosDataFilePath: string;
  let labelledDataFilePath: string;
  let mergedDataFilePath: string;
  let chunksDirectory: string;
  let videoChunks: string[] = [];
  let verifiedDataFilePath: string;

  // 1 Check that the path exists
  const pathExists = await exists(dataPath);
  if (!pathExists) {
    console.error(`Path does not exist: ${dataPath}`);
    return "errored";
  }

  // 2. Check that the path is a directory
  const isDir = await isDirectory(dataPath);
  if (!isDir) {
    console.error(`Path is not a directory: ${dataPath}`);
    return "errored";
  }

  // 3. Check that the directory is not empty
  const directoryContents = await readDir(dataPath);
  if (directoryContents.length === 0) {
    console.error(`Directory is empty: ${dataPath}`);
    return "errored";
  }

  // 4. Save the dirname as a variable: importedFolderName
  const folderName = dataPath.split("/").pop();
  if (!folderName) {
    console.error(`Could not get folder name from path: ${dataPath}`);
    return "errored";
  }
  importedFolderName = folderName;

  // 5. Chek that the directory contains 2 files: {importedFolderName}.json and {importedFolderName}.mov
  const jsonFilePath = await join(dataPath, `${importedFolderName}.json`);
  const movFilePath = await join(dataPath, `${importedFolderName}.mov`);
  if (!(await exists(jsonFilePath)) || !(await exists(movFilePath))) {
    console.error(`Missing required files: ${jsonFilePath}, ${movFilePath}`);
    return "errored";
  }

  // 6. Check that the {importedFolderName}.json file is valid JSON and not empty
  const isJsonValid = await jsonFileHasContent(jsonFilePath);
  if (!isJsonValid) {
    console.error(`Invalid or empty JSON file: ${jsonFilePath}`);
    return "errored";
  }

  // 7. Save the paths to each as vars to use later: motionDataJsonFilePath and originalImportedVideoFilePath
  motionDataJsonFilePath = jsonFilePath;
  originalImportedVideoFilePath = movFilePath;

  // 9. Check the directory for a file that startsWith(mov_info) and endsWith(.json)
  const movInfoFile = directoryContents.find(
    (file) => file.name?.startsWith(movInfoFileName) && file.name?.endsWith(".json")
  );

  // 10. Check that the mov_info file is valid JSON and not empty
  if (
    !movInfoFile ||
    !(await jsonFileHasContent(await join(dataPath, movInfoFile.name)))
  ) {
    console.error(
      "mov_info file missing or invalid, running collectMovInfo..."
    );
    const collectMovInfo = await runCollectMovInfo(dataPath, movInfoFileName);
    console.log("Command output:", collectMovInfo);
    return "processing";
  }

  // 12. if 9. and 10 pass  save the movInfo file path as a var: movInfoFilePath.
  movInfoFilePath = await join(dataPath, movInfoFile.name);

  // 18. Check the directory for a file that startsWith(step1_points_data) and endsWith(.csv)
  const pointsDataFile = directoryContents.find(
    (file) =>
      file.name?.startsWith(processVisualsCsvFileName) && file.name?.endsWith(".csv")
  );

  if (
    !pointsDataFile ||
    !(await csvFileHasContent(await join(dataPath, pointsDataFile.name)))
  ) {
    console.error(
      "step1_points_data.csv missing or empty, running processVisuals..."
    );
    const outputVideo = outputProcessedVideo ? "True" : "False";
    const processVisuals = await runProcessVisuals(dataPath, processVisualsCsvFileName, outputVideo);
    console.log("Command output:", processVisuals);
    return "processing";
  }

  pointsDataFilePath = await join(dataPath, pointsDataFile.name);

  // 22. if haveOutputVideo Check the directory for a file that startsWith(step1_processed_video) and endsWith(.mp4)
  if (outputProcessedVideo) {
    const processedVideoFile = directoryContents.find(
      (file) =>
        file.name?.startsWith(processVisualsCsvFileName) &&
        file.name?.endsWith(".mp4")
    );

    if (!processedVideoFile) {
      console.warn("Processed video missing.");
    } else {
      processedVideoFilePath = await join(dataPath, processedVideoFile.name);
    }
  }

  // 26. Check the directory for a file that startsWith(step1_ratios) and endsWith(.csv)
  const ratiosFile = directoryContents.find(
    (file) =>
      file.name?.startsWith(compareVisualsCsvFileName) && file.name?.endsWith(".csv")
  );

  if (
    !ratiosFile ||
    !(await csvFileHasContent(await join(dataPath, ratiosFile.name)))
  ) {
    console.error(
      `${compareVisualsCsvFileName}.csv missing or empty, running computeRatios...`
    );
    const runComputes = await runComputeRatios(dataPath, pointsDataFilePath, compareVisualsCsvFileName);
    console.log("Command output:", runComputes);
    return "processing";
  }

  ratiosDataFilePath = await join(dataPath, ratiosFile.name);

  // 30. Check the directory for a file that startsWith(labelled_data) and endsWith(.json)
  const labelledDataFile = directoryContents.find(
    (file) =>
      file.name?.startsWith(labelledJsonStartsWithString) &&
      file.name?.endsWith(".json")
  );

  if (!labelledDataFile) {
    console.error("labelled.json missing, waiting for user.");
    return "waiting";
  }

  labelledDataFilePath = await join(dataPath, labelledDataFile.name);
  const labelledDataContent = await readTextFile(labelledDataFilePath);

  try {
    const labelledData = JSON.parse(labelledDataContent);

    console.log("labelledData", labelledData);

    if (!Array.isArray(labelledData) || labelledData.length === 0) {
      console.error(
        "Labelling data is not in expected format, waiting for user."
      );
      return "errored";
    }

    // find the object with the key "status" and use it's value for the labelledDataStatus
    const status = labelledData.find(
      (data) => typeof data === "object" && "status" in data
    );
    if (status) {
      console.log("Labelled data status:", status.status);

      if (status.status === "complete") {
        console.log("Labelled data is complete.");

        // If there is no other content besides the {status: "complete"} object, return "errored"
        if (Object.keys(labelledData).length === 1) {
          console.error("Labelled data is empty, waiting for user.");
          return "errored";
        }
      } else if (status.status === "error") {
        console.error("Labelled data contains errors, waiting for user.");
        return "errored";
      } else {
        console.error("Labelled data is incomplete, waiting for user.");
        return "waiting";
      }
    } else {
      console.error("Labelled data is missing status, waiting for user.");
      return "errored";
    }
  } catch (error) {
    console.error("Error parsing labelled.json:", error);
    return "errored";
  }

  // 35. Check the directory for a file that startsWith(merged_data) and endsWith(.csv)
  const mergedDataFile = directoryContents.find(
    (file) =>
      file.name?.startsWith(mergedCsvFileName) && file.name?.endsWith(".csv")
  );

  if (
    !mergedDataFile ||
    !(await csvFileHasContent(await join(dataPath, mergedDataFile.name)))
  ) {
    console.error("merged_data.csv missing or empty, running merge...");
    const mergedOutput = await runMergeLabels(
      dataPath,
      labelledDataFilePath,
      movInfoFilePath,
      mergedCsvFileName
    );
    console.log("Command output:", mergedOutput);
    return "processing";
  }
  mergedDataFilePath = await join(dataPath, mergedDataFile.name);

  const chunksDirectoryPath = directoryContents.find(
    (dir) => dir.name?.startsWith(chunksDirectoryName) && dir.isDirectory
  );

  if (!chunksDirectoryPath) {
    console.error("Chunks directory missing. Running chunks command...");
    console.log(
      "Running get_chunks with:",
      dataPath,
      originalImportedVideoFilePath,
      mergedDataFilePath,
      chunksDirectoryName
    );
    const chunksOutput = await runGetChunks(
      dataPath,
      originalImportedVideoFilePath,
      mergedDataFilePath,
      chunksDirectoryName
    );
    console.log("Command output:", chunksOutput);
    return "processing";
  } else {
    // Check that the directory is not empty
    const chunksDirectoryContents = await readDir(
      await join(dataPath, chunksDirectoryPath.name)
    );
    if (chunksDirectoryContents.length === 0) {
      console.error(`Chunks directory is empty: ${chunksDirectoryPath.name}`);
      return "errored";
    } else {
      videoChunks = chunksDirectoryContents.map((file) => file.name);

      // Check that videoChunks.contains(startsWith("records") && endsWith(".json"))
      const recordsJson = videoChunks.find(
        (chunk) => chunk.startsWith("records") && chunk.endsWith(".csv")
      );
      if (!recordsJson) {
        console.error("records.json missing from chunks directory.");
        return "processing";
      } 
    }
  }

  chunksDirectory = await join(dataPath, chunksDirectoryPath.name);


  const verifiedDataFile = directoryContents.find(
    (file) =>
      file.name?.startsWith(verifiedJsonStartsWithString) &&
      file.name?.endsWith(".json")
  );

  if (!verifiedDataFile) {
    console.error("verified_data.json missing. Creating verified_data.json...");
    // Create the verified_data.json file
    const fileName = await join(
      dataPath,
      verifiedJsonStartsWithString + ".json"
    );
    const verifiedData = await createVerifiedJson(
      chunksDirectory,
      videoChunks,
      fileName
    );

    if (!verifiedData) {
      console.error("Error creating verified_data.json");
      return "errored";
    }
    console.log(
      "verified_data.json created successfully. Waiting for user to verify..."
    );
    return "waiting";
  }

  verifiedDataFilePath = await join(dataPath, verifiedDataFile.name);

  const verifiedDataContent = await readTextFile(verifiedDataFilePath);
  const verifiedData = JSON.parse(verifiedDataContent);

  if (!verifiedData || verifiedData.status !== "complete") {
    console.error("Verification incomplete, waiting for user.");
    return "waiting";
  }

  // 20. If verified_data contains fixes, trigger merge again
  if (Object.keys(verifiedData).length > 1) {
    // Check if any of the objects have "correct" set to false
    const incorrectData: VideoChunkStatus[] = verifiedData.filter(
      (data: any) => data.correct === false
    );

    if (incorrectData.length > 0) {
      console.error("Relabel data and run merge again.");
      return "waiting";
    } 
  }
  console.log(
    "Unused vars in taskProcessor.ts:",
    importedDataParentFolderName,
    mainThumbnailPath,
    scrubbingThumbnailsPaths,
    processedVideoFilePath,
    ratiosDataFilePath,
    motionDataJsonFilePath
  );

  return "completed";
}
