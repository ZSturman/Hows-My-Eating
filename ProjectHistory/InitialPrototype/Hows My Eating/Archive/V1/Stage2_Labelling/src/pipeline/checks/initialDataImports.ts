import { isDirectory } from "../../utilities/directoryChecks";
import { exists } from "@tauri-apps/plugin-fs";
import { join } from "@tauri-apps/api/path";
import { ChewingDataState } from "../../types/ChewingData.types";

export const checkInitialDataImports = async (data: ChewingDataState): Promise<boolean> => {
    const originalImportedFolderPath = data.originalImportedFolderPath;
    
    // Check that the import folder exists
    const originalImportedFolderExists = await checkFolderExists(originalImportedFolderPath);
    if (!originalImportedFolderExists) {
        console.error(`Original imported folder does not exist: ${originalImportedFolderPath}`);
        return false;
    }

    // Check that the import path is a directory and not a file
    const originalImportedFolderIsDirectory = await isDirectory(originalImportedFolderPath);
    if (!originalImportedFolderIsDirectory) {
        console.error(`Original imported folder is not a directory: ${originalImportedFolderPath}`);
        return false
    }


    // Check that the import folder contains the mov and the json files
    const movFile = data.originalMovFilePath
    const jsonFile = data.originalMotionDataJsonFilePath
    const originalImportedFolderContainsFiles = await checkFolderContainsFiles(originalImportedFolderPath, movFile, jsonFile);

    if (!originalImportedFolderContainsFiles) {
        console.error(`Original imported folder does not contain the required files: ${originalImportedFolderPath}`);
        return false;
    }

    return true;

}

const checkFolderExists = async (folderPath: string): Promise<boolean> => {
    try {
        const folderExists = await exists(folderPath);
        return folderExists;
    } catch (error) {
        console.error(`Error checking folder exists: ${folderPath}`, error);
        return false;
    }
}

const checkFolderContainsFiles = async (folderPath: string, movFile: string, jsonFile: string): Promise<boolean> => {
    try {
        const movFileExists = await exists(await join(folderPath, movFile));
        const jsonFileExists = await exists(await join(folderPath, jsonFile));
        return movFileExists && jsonFileExists;
    }
    catch (error) {
        console.error(`Error checking folder contains files: ${folderPath}`, error);
        return false;
    }
}