import { verifyFilePath } from "../validations/validataData";
import { CollectMovInfoOutput } from "../../types/ChewingData.types";
import { MovInfo } from "../../types/ChewingData.types";
import { fileHasContent } from "../../utilities/fileChecks";
import { exists, readTextFile } from "@tauri-apps/plugin-fs";

/**
 * Checks if the data item has all the required data for the Collect Mov Info step.
 * @param data The ChewingDataState item to check.
 * @returns True if all required data is present and valid, false otherwise.
 */
const collectMovInfoFileValidations = async (
  movInfo: MovInfo | null,
  data: CollectMovInfoOutput,
  mainThumbnailRequired: boolean,
  scrubbingThumbnailsRequired: boolean
): Promise<ReturnStatus> => {
  try {
    const movInfoFilePath = data.movInfoFilePath;
    if (!movInfoFilePath) {
      return {
        status: "error",
        data: "No movInfoFilePath provided",
      };
    }
    if (!movInfo) {
      // Check the data.collectMovInfo.movInfoFilePath first
      const movDataFromFile = await getMovInfoUsingSavedFilePath(
        movInfoFilePath
      );
      if (movDataFromFile === false) {
        return {
          status: "error",
          data: "Could not get movInfo from file",
        };
      }
      // TODO: Update movInfo in our state item here using movDataFromFile then do this check again
    }

    const movInfoFileVerified = await verifyFilePath(
      data.movInfoFilePath,
      "json"
    );
    if (!movInfoFileVerified) {
      console.error("Mov Info file not verified");
      return {
        status: "error",
        data: "Mov Info file not verified",
      };
    }

    const movInfoFileNotEmpty = await fileHasContent(data.movInfoFilePath);
    if (!movInfoFileNotEmpty) {
      console.error("Mov Info file is empty");
      return {
        status: "error",
        data: "Mov Info file is empty",
      };
    }

    if (mainThumbnailRequired) {
      const mainThumbnailVerified = await verifyFilePath(
        data.mainThumbnailPath,
        "jpg"
      );
      if (!mainThumbnailVerified) {
        console.error("Main Thumbnail not verified");
        return {
          status: "error",
          data: "Main Thumbnail not verified",
        };
      }
    }

    if (scrubbingThumbnailsRequired) {
      const scrubbingThumbnailsVerified = await Promise.all(
        data.scrubbingThumbnailsPaths.map((path) => verifyFilePath(path, "jpg"))
      );
      if (!scrubbingThumbnailsVerified) {
        console.error("Scrubbing Thumbnails not verified");
        return {
          status: "error",
          data: "Scrubbing Thumbnails not verified",
        };
      }
    }

    return {
      status: "success",
      data: undefined,
    };
  } catch (error) {
    console.error("Error in collectMovInfoFileValidations", error);
    return {
      status: "error",
      data: `Error in collectMovInfoFileValidations: ${error}`,
    };
  }
};

export default collectMovInfoFileValidations;

const getMovInfoUsingSavedFilePath = async (movInfoFilePath: string) => {
  const fileExists = await exists(movInfoFilePath);

  if (!fileExists) {
    console.error("Mov Info file not found");
    return false;
  }

  // Read the file and see if it's valid JSON
  const movInfoFile = await readTextFile(movInfoFilePath);
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


