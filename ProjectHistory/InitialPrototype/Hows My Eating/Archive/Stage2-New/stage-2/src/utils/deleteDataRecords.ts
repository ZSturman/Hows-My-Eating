import {
    readDir,
    BaseDirectory,
    exists,
    removeFile,
    removeDir,
  } from "@tauri-apps/api/fs";
  import { createErrorResponse, createSuccessResponse } from "./customResponse";
import { AppLog } from "../context/AppLogContext";
  
  export async function deleteDataFromAppData(dataDirectory: DataRecord): Promise<AppLog> {
const directoryToDelete = dataDirectory.dataDirectory;

    try {
      // Check if the data directory exists
      const directoryExists = await exists(directoryToDelete, {
        dir: BaseDirectory.AppData,
      });
  
      if (!directoryExists) {
        return createErrorResponse("Data directory does not exist.");
      }
  
      // Read the directory to get all files inside
      const entries = await readDir(directoryToDelete, { dir: BaseDirectory.AppData });
  
      if (!entries.length) {
        return createErrorResponse("Data directory is empty.");
      }
  
      // Delete all files in the directory
      for (const entry of entries) {
        if (entry.path) {
          await removeFile(entry.path, { dir: BaseDirectory.AppData });
          console.log(`Deleted file: ${entry.path}`);
        }
      }
  
      // Delete the data directory itself
      await removeDir(directoryToDelete, { dir: BaseDirectory.AppData, recursive: true });
      console.log(`Deleted directory: ${directoryToDelete}`);
  
      return createSuccessResponse(null, "Data deleted from AppData successfully.");
    } catch (error) {
      console.error("Error deleting data from AppData:", error);
      return createErrorResponse("Error deleting data from AppData.");
    }
  }