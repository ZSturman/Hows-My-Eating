import { DirEntry, readDir } from "@tauri-apps/plugin-fs";

/**
 * Checks if a JSON file exists in the provided directory contents.
 * @param contents - The directory contents.
 * @returns The first found JSON file, or `false` if none is found.
 */
export const hasJson = async (
  contents: DirEntry[]
): Promise<DirEntry | false> =>
  contents.find((file) => file.name?.endsWith(".json")) || false;

/**
 * Checks if a .mov file exists in the provided directory contents.
 * @param contents - The directory contents.
 * @returns The first found .mov file, or `false` if none is found.
 */
export const hasMov = async (contents: DirEntry[]): Promise<DirEntry | false> =>
  contents.find((file) => file.name?.endsWith(".mov")) || false;

/**
 * Determines if a given path is a directory.
 * @param path - The path to check.
 * @returns `true` if the path is a directory, otherwise `false`.
 */
export const isDirectory = async (path: string): Promise<boolean> => {
  try {
    const entries = await readDir(path);
    return Array.isArray(entries);
  } catch (error) {
    console.error(
      `Error reading path: ${path}`,
      error instanceof Error ? error.message : "Unknown error"
    );
    return false;
  }
};
