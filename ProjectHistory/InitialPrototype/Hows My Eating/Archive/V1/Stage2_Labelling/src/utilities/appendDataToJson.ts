import { ChewingDataState } from "@/types/ChewingData.types";
import { readTextFile, writeTextFile } from "@tauri-apps/plugin-fs";

const appendDataToJson = async (
  pathToTrackedDataJson: string,
  newData: ChewingDataState
): Promise<boolean> => {
  try {
    let existingData: ChewingDataState[] = [];

    // Attempt to read existing data
    try {
      const fileContents = await readTextFile(pathToTrackedDataJson);
      existingData = JSON.parse(fileContents);
      if (!Array.isArray(existingData)) {
        existingData = []; // Reset if the file is not an array
      }
    } catch (error) {
      console.warn("JSON file is empty or malformed. Creating a new array.");
      existingData = [];
    }

    // Append new data
    existingData.push(newData);

    // Write back to file
    await writeTextFile(pathToTrackedDataJson, JSON.stringify(existingData, null, 2));

    return true;
  } catch (error) {
    console.error("Error writing to JSON file:", error);
    return false;
  }
};

export default appendDataToJson;