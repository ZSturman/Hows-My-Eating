import { appDataDir, join } from '@tauri-apps/api/path';
import { readTextFile, writeTextFile, createDir, exists } from '@tauri-apps/api/fs';
import { AppRecord } from '../context/AppRecordContext';
import { AppLog } from '../context/AppLogContext';
import { initialAppRecord } from '../defaults/initialAppState';

const FILE_NAME = 'appRecord.json';
const LOG_FILE_NAME = 'appLogs.json';


// Import AppRecord from File
const importAppRecordFromFile = async (): Promise<AppRecord | null> => {
  try {
    const dir = await appDataDir();
    const path = await join(dir, FILE_NAME);

    // Check if the directory exists; if not, create it
    const dirExists = await exists(dir);
    if (!dirExists) {
      console.log('Directory does not exist, creating it:', dir);
      await createDir(dir, { recursive: true });
    }

    // Check if the file exists
    const fileExists = await exists(path);
    console.log('Checking if AppRecord file exists at path:', path, 'Exists:', fileExists);

    if (!fileExists) {
      console.log('File does not exist. Creating a new AppRecord file with default values.');
      await writeTextFile(path, JSON.stringify(initialAppRecord));
      console.log('Default AppRecord file created:', initialAppRecord);
      return initialAppRecord;
    }

    const fileContent = await readTextFile(path);
    const appRecord: AppRecord = JSON.parse(fileContent);
    console.log('AppRecord loaded from file:', appRecord);

    appRecord.sessions.push(Date.now()) // Update lastOpened on every load
    await writeTextFile(path, JSON.stringify(appRecord)); // Save the updated record
    console.log('Updated AppRecord with new lastOpened date:', appRecord);
    return appRecord;
  } catch (error) {
    console.error('Error importing AppRecord from file:', error);
    return null;
  }
};

// Export AppRecord to File
const exportAppRecordToFile = async (appRecord: AppRecord) => {
  try {
    console.log('Exporting AppRecord to file...');
    const dir = await appDataDir();
    const path = await join(dir, FILE_NAME);

    // Ensure the directory exists before writing the file
    const dirExists = await exists(dir);
    if (!dirExists) {
      console.log('Directory does not exist, creating it:', dir);
      await createDir(dir, { recursive: true });
    }

    await writeTextFile(path, JSON.stringify(appRecord));
    console.log('AppRecord exported to file:', appRecord);
  } catch (error) {
    console.error('Error exporting AppRecord to file:', error);
  }
};

// Save logs periodically
const saveLogsToFile = async (logs: AppLog[]) => {
  try {
    console.log('Saving logs to file...');
    const dir = await appDataDir();
    const path = await join(dir, LOG_FILE_NAME);

    // Ensure the directory exists before writing the logs
    const dirExists = await exists(dir);
    if (!dirExists) {
      console.log('Directory does not exist, creating it:', dir);
      await createDir(dir, { recursive: true });
    }

    await writeTextFile(path, JSON.stringify(logs));
    console.log('Logs saved to file:', path);
  } catch (error) {
    console.error('Error saving logs to file:', error);
  }
};

export {
  importAppRecordFromFile,
  exportAppRecordToFile,
  saveLogsToFile,
};
