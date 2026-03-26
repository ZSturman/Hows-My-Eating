import { hasJson, hasMov, isDirectory } from "./directoryChecks";
import { readDir } from "@tauri-apps/plugin-fs";
import copyFilesToAppDataDir from "./copyFiles";
//import appendDataToJson from "./appendDataToJson";

const importData = async (
  path: string,
  dataDirectory: string,
  importedFolderName: string
): Promise<ReturnStatus<string>> => {
  console.log("path", path);
  const { status, data } = await checkData(path);
  if (status === "error") {
    return {
      status: "error",
      data,
    };
  }

  const { jsonFilePath, movFilePath } = data;

  const filesCopiedOverResult = await copyFilesToAppDataDir(
    path,
    jsonFilePath,
    movFilePath,
    dataDirectory,
    importedFolderName
  );

  if (filesCopiedOverResult.status === "error") {
    return {
      status: "error",
      data: filesCopiedOverResult.data,
    };
  }


  return {
    status: "success",
    data: filesCopiedOverResult.data
  }
};

export default importData;

type RequiredDir = {
  jsonFilePath: string;
  movFilePath: string;
};

const checkData = async (path: string): Promise<ReturnStatus<RequiredDir>> => {
  if (!(await isDirectory(path))) {
    return {
      status: "error",
      data: "Path is not a directory.",
    };
  }

  const contents = await readDir(path);
  if (contents.length === 0) {
    return {
      status: "error",
      data: "Directory is empty.",
    };
  }

  const jsonFile = await hasJson(contents);
  if (!jsonFile) {
    return {
      status: "error",
      data: "Missing JSON file.",
    };
  }

  const movFile = await hasMov(contents);
  if (!movFile) {
    return {
      status: "error",
      data: "Missing MOV file.",
    };
  }

  return {
    status: "success",
    data: {
      jsonFilePath: jsonFile.name,
      movFilePath: movFile.name,
    },
  };
};

// /**
//  * @description Adds a new data entry to chewingDataState
//  * @param newData The NewImportedData object
//  */
// const constructChewingDataObject = async (
//   newData: NewImportedData
// ): Promise<ReturnStatus<ChewingDataState>> => {
//   try {
//     const newEntry: ChewingDataState = {
//       id: uuidv4(),
//       originalImportedFolderPath: newData.originalImportedFolderPath,
//       originalImportedFolderName: newData.originalImportedFolderName,
//       originalMovFilePath: newData.originalMovFilePath,
//       originalMotionDataJsonFilePath: newData.originalMotionDataJsonFilePath,
//       imported: newData.imported,
//       importedFolderPath: newData.importedFolderPath,
//       importedFolderName: newData.importedFolderName,
//       movInfo: null,
//       collectMovInfo: null,
//       processVisuals: null,
//       computeRatios: null,
//       manualLabeling: null,
//       mergeLabelsAndCsv: null,
//       verifyData: null,
//       exportData: null,
//       currentPipelineStep: 0,
//     };

//     return {
//       status: "success",
//       data: newEntry,
//     };
//   } catch (error) {
//     return {
//       status: "error",
//       data: `Error constructing new data entry: ${error}`,
//     };
//   }
// };
