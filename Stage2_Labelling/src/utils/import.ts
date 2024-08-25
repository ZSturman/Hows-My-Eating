import {
  readDir,
  BaseDirectory,
  exists,
  copyFile,
  createDir,
  writeTextFile
} from "@tauri-apps/api/fs";
import { basename } from "@tauri-apps/api/path";
import { desktopDir } from "@tauri-apps/api/path";
import { open } from "@tauri-apps/api/dialog";

export const handleOpenFileDialog = async (
  setMessages: React.Dispatch<React.SetStateAction<FlashMessage[]>>
) => {
  const selectedDirectory = await open({
    multiple: true,
    defaultPath: await desktopDir(),
    directory: true,
  });

  if (selectedDirectory) {
    if (Array.isArray(selectedDirectory)) {
      for (const dir of selectedDirectory) {
        // Validate the directory
        const validationMessages = await validateSelectedDirectory(dir);
        if (validationMessages.length > 0) {
          setMessages((prevMessages) => [
            ...prevMessages,
            ...validationMessages,
          ]);
        } else {
          // Save files to AppData
          const saveResult = await saveFilesToAppData(dir);
          setMessages((prevMessages) => [...prevMessages, ...saveResult]);
        }
      }
    } else {
      // Validate the directory
      const validationMessages = await validateSelectedDirectory(
        selectedDirectory
      );
      if (validationMessages.length > 0) {
        setMessages((prevMessages) => [...prevMessages, ...validationMessages]);
      } else {
        // Save files to AppData
        const saveResult = await saveFilesToAppData(selectedDirectory);
        setMessages((prevMessages) => [...prevMessages, ...saveResult]);
      }
    }
  }
};

export async function checkRequiredFiles(directory: string): Promise<{
  hasJson: boolean | string;
  hasMov: boolean | string;
  hasCsv: boolean | string;
  hasTrackingJson: boolean | string;
}> {
  try {
    const entries = await readDir(directory, { dir: BaseDirectory.AppData });

    let hasJson: boolean | string = false;
    let hasMov: boolean | string = false;
    let hasCsv: boolean | string = false;
    let hasTrackingJson: boolean | string = false;

    for (const entry of entries) {
      if (entry.name) {
        if (entry.name.endsWith(".json") && entry.name !== "tracking.json") {
          hasJson = entry.name;
        } else if (entry.name.endsWith(".mov")) {
          hasMov = entry.name;
        } else if (entry.name.endsWith(".csv")) {
          hasCsv = entry.name;
        } else if (entry.name === "tracking.json") {
          hasTrackingJson = entry.name;
        }
      }
    }

    return { hasJson, hasMov, hasCsv, hasTrackingJson };
  } catch (error) {
    console.error("Error reading directory:", error);
    return {
      hasJson: false,
      hasMov: false,
      hasCsv: false,
      hasTrackingJson: false,
    };
  }
}

export const validateSelectedDirectory = async (
  selectedDirectory: string
): Promise<FlashMessage[]> => {
  const validationMessages: FlashMessage[] = [];

  // Check that the directory exists
  const directoryExists = await exists(selectedDirectory, {
    dir: BaseDirectory.AppData,
  });
  if (!directoryExists) {
    const flashMessage = {
      title: "Error",
      message: "Selected directory does not exist.",
      type: "error" as "error",
    };
    validationMessages.push(flashMessage);
    return validationMessages;
  }

  // Check that the directory contains a .mov file and a .json file with matching names
  const hasRequiredFiles = await checkRequiredFiles(selectedDirectory);
  if (!hasRequiredFiles.hasJson || !hasRequiredFiles.hasMov) {
    if (!hasRequiredFiles.hasJson) {
      const flashMessage = {
        title: "Error",
        message:
          "Directory must contain a .json file matching the directory name.",
        type: "error" as "error",
      };
      validationMessages.push(flashMessage);
    }

    if (!hasRequiredFiles.hasMov) {
      const flashMessage = {
        title: "Error",
        message:
          "Directory must contain a .mov file matching the directory name.",
        type: "error" as "error",
      };
      validationMessages.push(flashMessage);
    }
  }

  return validationMessages;
};

export async function saveFilesToAppData(
  sourceDirectory: string
): Promise<FlashMessage[]> {
  try {
    const appDataDirectory = "RecordedData";
    const base = await basename(sourceDirectory);

    // Create a directory in AppData to save the files
    const destinationDirectory = `${appDataDirectory}/${base}`;
    const parentDirectoryExists = await exists(destinationDirectory, {
      dir: BaseDirectory.AppData,
    });

    if (!parentDirectoryExists) {
      await createDir(destinationDirectory, {
        dir: BaseDirectory.AppData,
        recursive: true,
      });
    }

    const entries = await readDir(sourceDirectory, {
      dir: BaseDirectory.AppData,
    });

    // Iterate through the files in the source directory
    for (const entry of entries) {
      if (
        entry.name &&
        (entry.name.endsWith(".json") || entry.name.endsWith(".mov"))
      ) {
        const destinationPath = `${destinationDirectory}/${entry.name}`;
        await copyFile(entry.path, destinationPath, {
          dir: BaseDirectory.AppData,
        });
        console.log(`Copied ${entry.name} to ${destinationPath}`);
      }
    }

    // Create tracking.json file inside the destination directory
    const trackingJsonPath = `${destinationDirectory}/tracking.json`;
    const trackingJsonExists = await exists(trackingJsonPath, {
      dir: BaseDirectory.AppData,
    });

    if (!trackingJsonExists) {
      const trackingData: TrackingJson = {
        importedAt: new Date().toISOString(),
        path: sourceDirectory,
        synced: false,
        movLength: 0,
        jsonLength: 0,
        firstMotionTimestamp: 0,
        csvs: [],
      };
      await writeTextFile(
        trackingJsonPath,
        JSON.stringify(trackingData, null, 2),
        {
          dir: BaseDirectory.AppData,
        }
      );
      console.log(`Tracking JSON created at ${trackingJsonPath}`);
    }

    return [];
  } catch (error) {
    console.error("Error saving files to AppData:", error);
    return [
      {
        title: "Error",
        message: "An error occurred while saving files to AppData.",
        type: "error" as "error",
      },
    ];
  }
}



