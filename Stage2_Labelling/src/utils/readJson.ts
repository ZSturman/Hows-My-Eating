import { BaseDirectory, readTextFile } from '@tauri-apps/api/fs';
import Papa from "papaparse";

export const readJson = async (filePath: string): Promise<any> => {
  try {
    const fileContent = await readTextFile(filePath);
    return JSON.parse(fileContent);
  } catch (err) {
    console.error('Failed to read or parse JSON file:', err);
    throw err; // rethrow the error after logging it
  }
}

export const parseMotionData = async (filePath: string): Promise<MotionData[]> => {
  try {
    const fileContent = await readTextFile(filePath);
    const data = JSON.parse(fileContent);
    return Array.isArray(data) ? data : [data]; // Ensure it's always an array
  } catch (err) {
    console.error('Failed to read or parse motion data:', err);
    throw err; // rethrow the error after logging it
  }
};


export async function parseLabelData(csvFilePath: string): Promise<LabelledData[] | null> {
  try {
    const csvString = await readTextFile(csvFilePath, { dir: BaseDirectory.AppData });
    const parsedData = Papa.parse<LabelledData>(csvString, { header: true });

    if (parsedData.errors.length > 0) {
      console.error("Error parsing CSV file:", parsedData.errors);
      return null;
    }

    return parsedData.data;
  } catch (error) {
    console.error("Error reading CSV file:", error);
    return null;
  }
}