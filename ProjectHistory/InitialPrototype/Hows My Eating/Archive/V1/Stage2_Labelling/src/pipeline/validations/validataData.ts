import { exists, readTextFile } from "@tauri-apps/plugin-fs";
import {
  CollectMovInfoReturnedData,
  ComputeRatiosReturnedData,
  ProcessVisualsReturnedData,
} from "../commands/types";
import { MovInfo } from "../../types/ChewingData.types";

import { open } from "@tauri-apps/plugin-shell";
import { fileHasContent } from "../../utilities/fileChecks";




/**
 * Use this when the command completes but the mov_info wasn't returned. This will check if the file was created and is valid JSON.
 * @param collectedMovInfoData - The data returned from the collectMovInfo command.
 * @returns A Promise resolving to the MovInfo object or `false` if the file is not found or is invalid.
 */
export const getMovInfoFromFile = async (
  collectedMovInfoData: CollectMovInfoReturnedData
): Promise<MovInfo | false> => {
  // Check for the mov info files
  const fileExists = await exists(collectedMovInfoData.mov_info_file_path);
  if (!fileExists) {
    console.error("Mov Info file not found");
    return false;
  }

  // Read the file and see if it's valid JSON
  const movInfoFile = await readTextFile(
    collectedMovInfoData.mov_info_file_path
  );
  if (!movInfoFile) {
    console.error("Mov Info file is empty");
    return false;
  }

  try {
    const movInfo: MovInfo = JSON.parse(movInfoFile);
    if (!movInfo) {
      console.error("Mov Info file is not valid JSON");
      return false;
    }
    return movInfo;
  } catch (error) {
    console.error("Error parsing Mov Info file", error);
    return false;
  }
};

/**
 * Checks if a string is empty, null, or undefined.
 * @param value - The string to check.
 * @returns `true` if the string is not empty, null, or undefined, otherwise `false`.
 */
export const checkForEmptyOrNullOrUndefinedStrings = (
  value: string
): boolean => {
  return !(value === null || value === undefined || value.trim() === "");
};

/**
 * Checks if a file exists at the provided path.
 * @param path - The path to the file.
 * @returns `true` if the file exists, otherwise `false`.
 */
export const checkThatTheFileExists = async (
  path: string
): Promise<boolean> => {
  const fileExists = await exists(path);
  if (!fileExists) {
    return false;
  }
  return true;
};

/**
 * Verifies that a file path is valid.
 * @param data - The file path to verify.
 * @param ext - Optional file type to check against.
 * @returns `true` if the file path is valid, otherwise `false`.
 *
 * @example
 * ```typescript
 * const isValid = await verifyFilePath("path/to/file.json", "json");
 * if (!isValid) {
 *  console.error("Invalid file path");
 * }
 * ```
 */

type AvailableExtensions =
  | "mov"
  | "mp4"
  | "avi"
  | "mp3"
  | "wav"
  | "jpg"
  | "jpeg"
  | "png"
  | "webp"
  | "txt"
  | "md"
  | "json"
  | "csv"
  | "xml"
  | "yaml"
  | "yml"
  | "tsv";

type AvailableMediaTypes = "video" | "audio" | "image" | "text" | "structured";

const availableExtensions = [
  "mov",
  "mp4",
  "avi",
  "mp3",
  "wav",
  "jpg",
  "jpeg",
  "png",
  "webp",
  "txt",
  "md",
  "json",
  "csv",
  "xml",
  "yaml",
  "yml",
  "tsv",
];

const availableMediaTypes = ["video", "audio", "image", "text", "structured"];

const checkFileType = async (
  data: string,
  fileType: AvailableExtensions
): Promise<boolean> => {

  console.log("CHECK FILE TYPE:", data, fileType);
  if (!data.endsWith(`.${fileType}`)) {
    console.error(`File is not a .${fileType} file`);
    return false;
  }

  console.log(`File ${data} IS a .${fileType} file`);
  return true;
};

const checkMediaType = async (
  data: string,
  mediaType: AvailableMediaTypes
): Promise<boolean> => {
  switch (mediaType) {
    case "video":
      if (
        !data.endsWith(".mov") &&
        !data.endsWith(".mp4") &&
        !data.endsWith(".avi")
      ) {
        console.error("File is not a .mov, .mp4, or .avi file");
        return false;
      }
      break;
    case "audio":
      if (!data.endsWith(".mp3") && !data.endsWith(".wav")) {
        console.error("File is not a .mp3 or .wav file");
        return false;
      }
      break;
    case "image":
      if (
        !data.endsWith(".jpg") &&
        !data.endsWith(".jpeg") &&
        !data.endsWith(".png") &&
        !data.endsWith(".webp")
      ) {
        console.error("File is not a .jpg, .jpeg, .png, .gif, or .webp file");
        return false;
      }
      break;
    case "text":
      if (!data.endsWith(".txt") && !data.endsWith(".md")) {
        console.error("File is not a .txt or .md file");
        return false;
      }
      break;
    case "structured":
      if (
        !data.endsWith(".json") &&
        !data.endsWith(".csv") &&
        !data.endsWith(".xml") &&
        !data.endsWith(".yaml") &&
        !data.endsWith(".yml") &&
        !data.endsWith(".tsv")
      ) {
        console.error(
          "File is not a .json, .csv, .xml, .yaml, .yml, or .tsv file"
        );
        return false;
      }
      break;
  }

  return true;
};

export const verifyFilePath = async (
  data: string,
  fileType?: AvailableMediaTypes | AvailableExtensions
): Promise<boolean> => {

  console.log("VERIFY PATH:", data, fileType);
  if (!checkForEmptyOrNullOrUndefinedStrings(data)) {
    console.error("Empty or null file path");
    return false;
  }

  if (!(await checkThatTheFileExists(data))) {
    console.error("File does not exist");
    return false;
  }

  if (fileType) {
    if (availableMediaTypes.includes(fileType)) {
      if (!(await checkMediaType(data, fileType as AvailableMediaTypes))) {
        return false;
      } 
    } else if (availableExtensions.includes(fileType)) {
      console.log("CHECK FILE TYPE:", data, fileType);
      if (!(await checkFileType(data, fileType as AvailableExtensions))) {
        console.log(`File ${data} is not a .${fileType} file`);
        return false;
      } 
    } else {
      console.error("Invalid file type");
      return false;
    }
  }

  return true;
};

const verifyVideoDoesPlay = async (filePath: string): Promise<boolean> => {
  try {
    await open(filePath);
    return true;
  } catch (error) {
    console.error("Error opening video file:", error);
    return false;
  }
};





export const verifyProcessedVisualsData = async (
  data: ProcessVisualsReturnedData
): Promise<boolean> => {
  const pointsDataCsvFilePath = await verifyFilePath(data.csv_file_path, "csv");
  if (!pointsDataCsvFilePath) {
    console.error("Mov Info file not verified");
    return false;
  }

  const pointsDataCsvHasContent = await fileHasContent(data.csv_file_path);
    if (!pointsDataCsvHasContent) {
        console.error("Mov Info file is empty");
        return false;
    }

  if (data.video_file_path) {
    const outputVideoFilePath = await verifyFilePath(
      data.video_file_path,
      "video"
    );
    if (!outputVideoFilePath) {
      console.error("Main Thumbnail not verified");
      return false;
    }

    const videoDoesPlay = await verifyVideoDoesPlay(data.video_file_path);
    if (!videoDoesPlay) {
      console.error("Video does not play");
      return false;
    }
  }

  return true;
};

export const verifyComputeRatiosData = async (
  data: ComputeRatiosReturnedData
): Promise<boolean> => {
  const pointsDataCsvFilePath = await verifyFilePath(data.csv_file_path, "csv");
  if (!pointsDataCsvFilePath) {
    console.error("Mov Info file not verified");
    return false;
  }

  const pointsDataCsvHasContent = await fileHasContent(data.csv_file_path);
    if (!pointsDataCsvHasContent) {
        console.error("Mov Info file is empty");
        return false;
    }

  return true;
};
