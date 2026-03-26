import { exists, readTextFile, stat } from "@tauri-apps/plugin-fs";

export const fileHasContent = async (filePath: string): Promise<boolean> => {
  try {
    if (!(await exists(filePath))) {
      return false;
    }

    const fileMetadata = await stat(filePath);

    if (filePath.endsWith(".json")) {
      return await jsonFileHasContent(filePath);
    } else if (filePath.endsWith(".csv")) {
      return await csvFileHasContent(filePath);
    } else {
      return fileMetadata.size !== 0;
    }
  } catch (error) {
    console.error("Error checking file size:", error);
    return false; // Assume empty if there's an error
  }
};

export const jsonFileHasContent = async (
  filePath: string
): Promise<boolean> => {
  try {
    if (!(await exists(filePath))) {
      return false;
    }

    const fileContent = await readTextFile(filePath);

    // Check if file is completely empty
    if (!fileContent.trim()) {
      return false;
    }

    const parsedData = JSON.parse(fileContent);

    // Check if JSON is just an empty object `{}` or an empty array `[]`
    if (
      (typeof parsedData === "object" &&
        parsedData !== null &&
        Object.keys(parsedData).length === 0) ||
      (Array.isArray(parsedData) && parsedData.length === 0)
    ) {
      console.log("JSON file contains an empty object or array.");
      return false;
    }

    return true;
  } catch (error) {
    console.error("Error reading or parsing JSON file:", error);
    return false; // Assume empty or invalid if there's an error
  }
};

export const csvFileHasContent = async (
  filePath: string,
  hasHeader = true
): Promise<boolean> => {
  try {
    if (!(await exists(filePath))) {
      console.error("CSV file does not exist.");
      return false;
    }

    const fileContent = await readTextFile(filePath);
    const rows = fileContent.split("\n").filter((row) => row.trim() !== "");

    if (hasHeader && rows.length <= 1) {
      console.error("CSV file does not contain data beyond the header.");
      return false;
    }

    return rows.length > 0;
  } catch (error) {
    console.error("Error reading CSV file:", error);
    return false;
  }
};
