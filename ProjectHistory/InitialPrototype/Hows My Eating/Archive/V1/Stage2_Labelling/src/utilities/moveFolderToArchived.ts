import { join } from "@tauri-apps/api/path";
import { isValidState } from "./isValid";
import {
  copyFile,
  DirEntry,
  exists,
  mkdir,
  readDir,
} from "@tauri-apps/plugin-fs";

const moveFolderToArchived = async (
  sourceDir: string,
  dataDirectory: string,
  archiveFolderName: string
): Promise<ReturnStatus<string>> => {
  const dataDir = isValidState(dataDirectory);

  if (!dataDir) {
    return {
      status: "error",
      data: "Data directory not ready.",
    };
  }

  const validDataDir: string = dataDirectory;

  if (!dataDir) {
    return {
      status: "error",
      data: "Data directory not ready.",
    };
  }

  try {
    const dirName = sourceDir.split("/").pop() || "unknown";
    const targetDir = await join(validDataDir, archiveFolderName, dirName);

    if (!(await exists(targetDir))) {
      await mkdir(targetDir, { recursive: true });
    }

    const allFilesAndFolders: DirEntry[] = await readDir(sourceDir);

    console.log("ALL FILES AND FOLDERS", allFilesAndFolders);

    for (const file of allFilesAndFolders) {
      if (file.isDirectory) {
        console.log("IS DIRECTORY", file);
      }

      if (!file.isDirectory) {
        console.log("IS FILE", file);
        const targetFile = await join(targetDir, file.name);
        await copyFile(await join(sourceDir, file.name), targetFile);
      }
    }

    return { status: "success", data: targetDir };
  } catch (error) {
    return {
      status: "error",
      data: `Error copying files: ${error}`,
    };
  }
};

export default moveFolderToArchived;
