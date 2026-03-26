import {
  exists,
  readDir,
  mkdir,
  copyFile,
  readTextFile,
} from "@tauri-apps/plugin-fs";
import {  join } from "@tauri-apps/api/path";
import { isDirectory } from "../utilities/directoryChecks";
import { csvFileHasContent, jsonFileHasContent } from "./fileChecks";
import { runExport } from "../pipeline/commands/exporting";

export const handleExportData = async (
  saveLocation: string,
  dataPath: string,
  appConfig: AppConfig
): Promise<{ success: boolean; message: string }> => {

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
    const processVisualFileName = appConfig.processVisualsCsvFileName || "process-visuals";

    
  let importedFolderName: string;
  let motionDataJsonFilePath: string;
  let originalImportedVideoFilePath: string;
  const exportedFolderName: string = appConfig.exportFolderName || "exported";
  let movInfoFilePath: string;
  let processedVideoFilePath: string | null = null;
  let pointsDataFilePath: string;
  let ratiosDataFilePath: string;
  let mergedDataFilePath: string;
  let chunksDirectory: string;
  let chunksRecords: string;

  // 1 Check that the path exists
  const pathExists = await exists(dataPath);
  if (!pathExists) {
    console.error(`Path does not exist: ${dataPath}`);
    return { success: false, message: `${dataPath} does not exist` };
  }

  // 2. Check that the path is a directory
  const isDir = await isDirectory(dataPath);
  if (!isDir) {
    console.error(`Path is not a directory: ${dataPath}`);
    return { success: false, message: `${dataPath} is not a directory` };
  }

  // 3. Check that the directory is not empty
  const directoryContents = await readDir(dataPath);
  if (directoryContents.length === 0) {
    console.error(`Directory is empty: ${dataPath}`);
    return { success: false, message: `${dataPath} is empty` };
  }

  // 4. Save the dirname as a variable: importedFolderName
  const folderName = dataPath.split("/").pop();
  if (!folderName) {
    console.error(`Could not get folder name from path: ${dataPath}`);
    return {
      success: false,
      message: `Could not get folder name from path: ${dataPath}`,
    };
  }
  importedFolderName = folderName;

  console.log("Imported Folder Name:", importedFolderName);

  const jsonFilePath = await join(dataPath, `${importedFolderName}.json`);
  const movFilePath = await join(dataPath, `${importedFolderName}.mov`);
  if (!(await exists(jsonFilePath)) || !(await exists(movFilePath))) {
    console.error(`Missing required files: ${jsonFilePath}, ${movFilePath}`);
    return {
      success: false,
      message: `Missing required files: ${jsonFilePath}, ${movFilePath}`,
    };
  }

  // 6. Check that the {importedFolderName}.json file is valid JSON and not empty
  const isJsonValid = await jsonFileHasContent(jsonFilePath);
  if (!isJsonValid) {
    console.error(`Invalid or empty JSON file: ${jsonFilePath}`);
    return {
      success: false,
      message: `Invalid or empty JSON file: ${jsonFilePath}`,
    };
  }

  motionDataJsonFilePath = jsonFilePath;
  originalImportedVideoFilePath = movFilePath;

  const movInfoFile = directoryContents.find(
    (file) => file.name?.startsWith(
      movInfoFileName
    ) && file.name?.endsWith(".json")
  );

  // 10. Check that the mov_info file is valid JSON and not empty
  if (
    !movInfoFile ||
    !(await jsonFileHasContent(await join(dataPath, movInfoFile.name)))
  ) {
    return {
      success: false,
      message: `Invalid or empty JSON file: ${movInfoFile?.name}`,
    };
  }

  // 12. if 9. and 10 pass  save the movInfo file path as a var: movInfoFilePath.
  movInfoFilePath = await join(dataPath, movInfoFile.name);

  if (outputProcessedVideo) {
    const processedVideoFile = directoryContents.find(
      (file) =>
        file.name?.startsWith(processVisualFileName) &&
        file.name?.endsWith(".mp4")
    );

    if (!processedVideoFile) {
      console.warn("Processed video missing.");
    } else {
      processedVideoFilePath = await join(dataPath, processedVideoFile.name);
    }
  }

  const pointsDataFile = directoryContents.find(
    (file) =>
      file.name?.startsWith(processVisualFileName) && file.name?.endsWith(".csv")
  );

  if (
    !pointsDataFile ||
    !(await csvFileHasContent(await join(dataPath, pointsDataFile.name)))
  ) {
    return {
      success: false,
      message: `Invalid or empty CSV file: ${pointsDataFile?.name}`,
    };
  }

  pointsDataFilePath = await join(dataPath, pointsDataFile.name);

  const ratiosFile = directoryContents.find(
    (file) =>
      file.name?.startsWith(compareVisualsCsvFileName) && file.name?.endsWith(".csv")
  );

  if (
    !ratiosFile ||
    !(await csvFileHasContent(await join(dataPath, ratiosFile.name)))
  ) {
    return {
      success: false,
      message: `Invalid or empty CSV file: ${ratiosFile?.name}`,
    };
  }

  ratiosDataFilePath = await join(dataPath, ratiosFile.name);

  const mergedDataFile = directoryContents.find(
    (file) =>
      file.name?.startsWith(mergedCsvFileName) && file.name?.endsWith(".csv")
  );

  if (
    !mergedDataFile ||
    !(await csvFileHasContent(await join(dataPath, mergedDataFile.name)))
  ) {
    return {
      success: false,
      message: `Invalid or empty CSV file: ${mergedDataFile?.name}`,
    };
  }
  mergedDataFilePath = await join(dataPath, mergedDataFile.name);

  const chunksDirectoryPath = directoryContents.find(
    (dir) => dir.name?.startsWith(chunksDirectoryName) && dir.isDirectory
  );

  if (!chunksDirectoryPath) {
    return {
      success: false,
      message: `Missing required directory: ${chunksDirectoryName}`,
    };
  }

  // Check that the directory is not empty
  const chunksDirectoryContents = await readDir(
    await join(dataPath, chunksDirectoryPath.name)
  );
  if (chunksDirectoryContents.length === 0) {
    return {
      success: false,
      message: `Directory is empty: ${chunksDirectoryPath.name}`,
    };
  }

  chunksDirectory = await join(dataPath, chunksDirectoryPath.name);

  const recordsFilePath = chunksDirectoryContents.find(
    (file) => file.name === "records.csv"
  );

  if (!recordsFilePath) {
    return {
      success: false,
      message: `Missing required directory: ${chunksDirectoryName}`,
    };
  }

  chunksRecords = await join(chunksDirectory, recordsFilePath.name);

  console.log("All records exist. Continuing...");

  // Step 0. Create an "exported" folder in the desginated location. In that folder create another folder named the same as the final part of the dataPath.
  const exportedFolder = await join(saveLocation, exportedFolderName);
  const exportedProjectFolder = await join(exportedFolder, importedFolderName);
  await mkdir(exportedFolder, { recursive: true });
  await mkdir(exportedProjectFolder, { recursive: true });

  const extraDataFiles: string[] = [
    motionDataJsonFilePath,
    originalImportedVideoFilePath,
    movInfoFilePath,
    pointsDataFilePath,
    ratiosDataFilePath,
    mergedDataFilePath,
    chunksRecords,
  ];

  if (outputProcessedVideo && processedVideoFilePath) {
    extraDataFiles.push(processedVideoFilePath);
  }

  const extraDataFolder = await join(exportedProjectFolder, "extra");
  await mkdir(extraDataFolder, { recursive: true });

  extraDataFiles.forEach(async (file) => {
    const fileName = file.split("/").pop();
    if (!fileName || fileName === undefined) {
      console.error(`Could not get file name from path: ${file}`);
      return;
    }
    const saveLocation = await join(extraDataFolder, fileName);
    await copyFile(file, saveLocation);
  });

  const success = await runExport(
    dataPath,
    exportedProjectFolder,
    motionDataJsonFilePath,
    movInfoFilePath,
    ratiosDataFilePath,
    pointsDataFilePath,
    mergedDataFilePath,
    chunksDirectory,
    chunksRecords
  );

  if (success) {
    const toCopyOver = await join(
      dataPath,
      chunksDirectoryName,
      "to_copy.json"
    );

    if (await exists(toCopyOver)) {
      const toCopyOverContents = await readTextFile(toCopyOver);

      const toCopyContent = JSON.parse(toCopyOverContents);

      // Check that it is an array
      if (!Array.isArray(toCopyContent)) {
        console.error("to_copy.json is not an array");
        return {
          success: false,
          message: "to_copy.json is not an array",
        };
      }

      toCopyContent.forEach(
        async (file: { folder_path: string; file_path: string }) => {
          const fileName = file.file_path.split("/").pop();

          if (!fileName || fileName === undefined) {
            console.error(
              `Could not get file name from path: ${file.file_path}`
            );
            return;
          }

          console.log("Copying file:", file);
          console.log("File Path:", file.file_path);
          console.log("Folder Path:", file.folder_path);

          const saveLocation = await join(file.folder_path, fileName);

          await copyFile(file.file_path, saveLocation);
        }
      );
    }

    return { success: true, message: "Data exported successfully" };
  } else {
    return { success: false, message: "Data export failed" };
  }
};
