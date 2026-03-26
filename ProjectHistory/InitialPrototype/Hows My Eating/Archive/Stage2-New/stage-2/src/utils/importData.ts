import {
  readDir,
  BaseDirectory,
  exists,
  copyFile,
  createDir,
  writeTextFile,
} from "@tauri-apps/api/fs";
import { basename, resolveResource } from "@tauri-apps/api/path";
import { createErrorResponse, createSuccessResponse } from "./customResponse";
import { initialDataRecord } from "../defaults/initialAppState";
import { Command } from '@tauri-apps/api/shell';
import { AppLog } from "../context/AppLogContext";



export async function getMovInfo(filePath: string) {
  try {
    // Resolve the path to the executable using resolveResource
    await resolveResource('bin/get_mov_info');
    const command = Command.sidecar('bin/get_mov_info', [filePath]);
    
    const output = await command.execute();

    if (output.code === 0) {
      const info = JSON.parse(output.stdout.trim());
      return {
        duration: info.duration,
        width: info.width,
        height: info.height,
        fps: info.fps,
        totalFrams: info.total_frames,
      };
    } else {
      console.error('Error running executable:', output.stderr);
      return null;
    }
  } catch (error) {
    console.error('Error getting MOV file information:', error);
    return null;
  }
}


export async function extractAudio(filePath: string) {
  try {
    await resolveResource('bin/extract_audio');
    const command = Command.sidecar('bin/extract_audio', [filePath]);
    
    const output = await command.execute();

    if (output.code === 0) {
      const audioInfo = JSON.parse(output.stdout.trim());
      return {
        duration: audioInfo.duration,
        channels: audioInfo.channels,
        sampleRate: audioInfo.sample_rate,
        outputPath: audioInfo.output_path,
      };
    } else {
      console.error('Error extracting audio:', output.stderr);
      return null;
    }
  } catch (error) {
    console.error('Error extracting audio from MOV file:', error);
    return null;
  }
}

export async function getMotionInfo(filePath: string) {
  try {
    // Resolve the path to the executable using resolveResource
    await resolveResource('bin/get_motion_data_info');
    const command = Command.sidecar('bin/get_motion_data_info', [filePath]);
    
    const output = await command.execute();

    if (output.code === 0) {
      const duration = JSON.parse(output.stdout.trim());
      return {
        totalDuration: duration,
      };
    } else {
      console.error('Error running executable:', output.stderr);
      return null;
    }
  } catch (error) {
    console.error('Error getting Moton Data information:', error);
    return null;
  }
}

export async function generateCsv(filePath: string) {
  try {
    // Resolve the path to the executable using resolveResource
    await resolveResource('bin/create_csv');
    const command = Command.sidecar('bin/create_csv', [filePath]);

    const output = await command.execute();

    if (output.code === 0) {
      // Ensure the output is valid JSON
      try {
        const csvData = JSON.parse(output.stdout.trim());
        return {
          csvPath: csvData.csv_path,
          numberOfEntries: csvData.total_entries,
        };
      } catch (parseError) {
        console.error('Error parsing CSV generation output:', parseError);
        return null;
      }
    } else {
      console.error('Error running executable:', output.stderr);
      return null;
    }
  } catch (error) {
    console.error('Error generating CSV:', error);
    return null;
  }
}




export async function checkRequiredFiles(directory: string): Promise<{
  hasJson: boolean | string;
  hasMov: boolean | string;
  
}> {
  try {
    const entries = await readDir(directory, { dir: BaseDirectory.AppData });

    let hasJson: boolean | string = false;
    let hasMov: boolean | string = false;

    for (const entry of entries) {
      if (entry.name) {
        if (entry.name.endsWith(".json") && entry.name !== "data_record.json") {
          hasJson = entry.name;
        } else if (entry.name.endsWith(".mov")) {
          hasMov = entry.name;
        } 
      }
    }

    return { hasJson, hasMov };
  } catch (error) {
    console.error("Error reading directory:", error);
    return {
      hasJson: false,
      hasMov: false,
    };
  }
}

export const validateSelectedDirectory = async (
  selectedDirectory: string
): Promise<AppLog> => {
  // Check that the directory exists
  const directoryExists = await exists(selectedDirectory, {
    dir: BaseDirectory.AppData,
  });
  if (!directoryExists) {
    return createErrorResponse("Directory does not exist.");
  }

  // Check that the directory contains a .mov file and a .json file with matching names
  const hasRequiredFiles = await checkRequiredFiles(selectedDirectory);
  if (!hasRequiredFiles.hasJson || !hasRequiredFiles.hasMov) {
    if (!hasRequiredFiles.hasJson) {
      return createErrorResponse("Directory does not contain a JSON file.");
    }

    if (!hasRequiredFiles.hasMov) {
      return createErrorResponse("Directory does not contain a MOV file.");
    }
  }
  return createSuccessResponse(hasRequiredFiles, "Directory is valid.");
};

export async function saveFilesToAppData(
  sourceDirectory: string,
): Promise<AppLog> {
  try {
    const appDataDirectory = "DataRecords";
    const base = await basename(sourceDirectory);

    // Create a directory in AppData to save the files
    const destinationDirectory = `${appDataDirectory}/${base}`;
    const parentDirectoryExists = await exists(destinationDirectory, {
      dir: BaseDirectory.AppData,
    });

    if (parentDirectoryExists) {
      return createErrorResponse(`Data record already exists at ${destinationDirectory}.`);
    } else {
      await createDir(destinationDirectory, {
        dir: BaseDirectory.AppData,
        recursive: true,
      });
    }

    const entries = await readDir(sourceDirectory, {
      dir: BaseDirectory.AppData,
    });

    const savedDataRecord: DataRecord = {
      ...initialDataRecord,
      dateAdded: Date.now(),
      lastModified: Date.now(),
      dataDirectory: destinationDirectory,
      originalDataPath: sourceDirectory,
    };

    // Iterate through the files in the source directory
    for (const entry of entries) {
      if (entry.name && entry.name.endsWith(".json")) {
        const motionDataInfo = await getMotionInfo(entry.path);
        if (motionDataInfo) {
          const destinationPath = `${destinationDirectory}/${base}.json`;
          await copyFile(entry.path, destinationPath, {
            dir: BaseDirectory.AppData,
          });
          savedDataRecord.motionData = {
            path: destinationPath,
            ...motionDataInfo.totalDuration,
          };

          console.log(`Copied ${entry.name} to ${destinationPath}`);
        }

        const csvData = await generateCsv(entry.path);
        if (csvData) {
          const destinationPath = `${destinationDirectory}/${base}.csv`;
          await copyFile(csvData.csvPath, destinationPath, {
            dir: BaseDirectory.AppData,
          });
          savedDataRecord.csvData = {
            path: destinationPath,
            totalRows: csvData.numberOfEntries,
          };
          savedDataRecord.motionData.totalEntries = csvData.numberOfEntries;
          console.log(`Created CSV at ${destinationPath}`);
        }

      } else if (entry.name && entry.name.endsWith(".mov")) {
        const movInfo = await getMovInfo(entry.path);
        if (movInfo) {
          const destinationPath = `${destinationDirectory}/${base}.mov`;
          await copyFile(entry.path, destinationPath, {
            dir: BaseDirectory.AppData,
          });
          savedDataRecord.movData = {
            path: destinationPath,
            duration: movInfo.duration,
            width: movInfo.width,
            height: movInfo.height,
            fps: movInfo.fps,
            totalFrames: movInfo.totalFrams,
          };
          console.log(`Copied ${entry.name} to ${destinationPath}`);
        }

        const audioInfo = await extractAudio(entry.path);
        if (audioInfo) {
          const destinationPath = `${destinationDirectory}/${base}.wav`;
          await copyFile(audioInfo.outputPath, destinationPath, {
            dir: BaseDirectory.AppData,
          });
          savedDataRecord.audioData = {
            path: destinationPath,
            duration: audioInfo.duration,
            channels: audioInfo.channels,
            sampleRate: audioInfo.sampleRate,
          };
        }
      }
    }

    // Create tracking.json file inside the destination directory
    const recordedDataRecordPath = `${destinationDirectory}/data_record.json`;
    const recordedDataRecordExists = await exists(recordedDataRecordPath, {
      dir: BaseDirectory.AppData,
    });

    if (!recordedDataRecordExists) {
      await writeTextFile(
        recordedDataRecordPath,
        JSON.stringify(savedDataRecord, null, 2),
        {
          dir: BaseDirectory.AppData,
        }
      );
      console.log(`Data Record JSON created at ${recordedDataRecordPath}`);
      return createSuccessResponse(savedDataRecord, "Files saved to AppData successfully.");
    } else {
      const newRecordedDataRecordPath = `${destinationDirectory}/data_record_${Date.now()}.json`;
      await writeTextFile(
        newRecordedDataRecordPath,
        JSON.stringify(savedDataRecord, null, 2),
        {
          dir: BaseDirectory.AppData,
        }
      );
      return createSuccessResponse(savedDataRecord, `Files saved to AppData successfully. Data record already existed so a duplicate was created at: ${newRecordedDataRecordPath}`);
    }
  } catch (error) {
    console.error("Error saving files to AppData:", error);
    return createErrorResponse("Error saving files to AppData.");
  }
}