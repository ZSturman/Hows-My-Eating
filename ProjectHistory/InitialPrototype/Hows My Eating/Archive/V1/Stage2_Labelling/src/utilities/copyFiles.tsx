import { join } from "@tauri-apps/api/path";
import { isValidState } from "./isValid";
import { copyFile, exists, mkdir } from "@tauri-apps/plugin-fs";

  const copyFilesToAppDataDir = async (
    sourceDir: string,
    jsonFile: string,
    movFile: string,
    dataDirectory: string,
    importedFolderName: string
  ): Promise<ReturnStatus<string>> => {

    console.log("dataDirectory", dataDirectory);  

    const dataDir = isValidState(dataDirectory)

    if (!dataDir) {
      return {
        status: "error",
        data: "Data directory not ready.",
      };
    }

    const validDataDir: string = dataDirectory

    console.log("validDataDir", validDataDir);

    if (!dataDir) { 
        return ({
            status: "error",
            data: "Data directory not ready.",
        });
    }

    try {
      const dirName = sourceDir.split("/").pop() || "unknown";
      const targetDir = await join(validDataDir, importedFolderName, dirName);

      if (!(await exists(targetDir))) {
        await mkdir(targetDir, { recursive: true });
      }

      const jsonSource = await join(sourceDir, jsonFile);
      const movSource = await join(sourceDir, movFile);
      const jsonTarget = await join(targetDir, jsonFile);
      const movTarget = await join(targetDir, movFile);

      await copyFile(jsonSource, jsonTarget);
      await copyFile(movSource, movTarget);

      return {status: "success",
        data: targetDir}
    } catch (error) {

      return {
        status: "error",
        data: `Error copying files: ${error}`,
      }
    }
  };

  export default copyFilesToAppDataDir;