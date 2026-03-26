import { Command } from "@tauri-apps/plugin-shell";
import { join } from "@tauri-apps/api/path";
import { sanitizeArg } from "../../utilities/commands";

export const runExport = async (
    dataPath: string,
    exportedProjectFolder: string,
    motionDataJsonFilePath: string,
    movInfoFilePath: string,
    ratiosDataFilePath: string,
    pointsDataFilePath: string,
    mergedDataFilePath: string,
    chunksDirectory: string,
    chunksRecords: string,
): Promise<boolean> => {
  console.log(
    "Running exporitng with", 
    exportedProjectFolder,
    motionDataJsonFilePath,
    movInfoFilePath,
    ratiosDataFilePath,
    pointsDataFilePath,
    mergedDataFilePath,
    chunksDirectory,
    chunksRecords
  );

  const logFile = await join(dataPath, "exporting.log");

  try {
    const args = [
        sanitizeArg(exportedProjectFolder),
        sanitizeArg(motionDataJsonFilePath),
        sanitizeArg(movInfoFilePath),
        sanitizeArg(ratiosDataFilePath),
        sanitizeArg(pointsDataFilePath),
        sanitizeArg(mergedDataFilePath),
        sanitizeArg(chunksDirectory),
        sanitizeArg(chunksRecords),
      "--log_file",
      sanitizeArg(logFile),
    ];

    // Use the sidecar binary that wraps your Python merge_labels function.
    const command = Command.sidecar("binaries/exporting", args);

    const output = await command.execute();

    console.log("OUTPUT:", output);

    // Filter out irrelevant stderr messages.
    const filteredStderr = output.stderr
      ? output.stderr
          .split("\n")
          .filter(
            (line) => !line.includes("Matplotlib is building the font cache")
          )
          .filter((line) => !line.includes("WARNING"))
          .filter((line) => !line.includes("SettingWithCopyWarning"))
          .filter((line) => !line.startsWith("pandas/core/generic.py"))
          .join("\n")
      : "";

    if (filteredStderr) {
      console.error("Chunk Videos Error (filtered):", filteredStderr);
    }

    if (output.stdout) {
      console.log("Raw chunks stdout:", output.stdout);

      try {
        // Look for a JSON response starting with {"success":
        const startIndex = output.stdout.indexOf('{"success":');
        if (startIndex === -1) {
          throw new Error("No valid JSON response found in the output.");
        }

        const jsonResponseString = output.stdout.slice(startIndex);
        const response = JSON.parse(jsonResponseString);

        // Expecting a response such as:
        if (response.success) {
          return true
        } else {
          return false
        }
      } catch (jsonError) {
        console.error("Failed to parse JSON response:", jsonError);
        return false
      }
    }

    return true
  } catch (error) {
    return false
  }
};