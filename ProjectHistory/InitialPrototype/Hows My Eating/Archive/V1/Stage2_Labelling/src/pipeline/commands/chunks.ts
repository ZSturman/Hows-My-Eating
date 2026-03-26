import { Command } from "@tauri-apps/plugin-shell";
import { join } from "@tauri-apps/api/path";
import { sanitizeArg } from "../../utilities/commands";
import { ChunksReturnedData } from "./types";

export const runGetChunks = async (
  dirpath: string,
  videoPath: string,
  mergedCsvPath: string,
  outputDirName: string
): Promise<ReturnStatus<ChunksReturnedData>> => {
  console.log(
    "Running chunks with:",
    videoPath,
    mergedCsvPath
  );

  const logFile = await join(dirpath, "chunks.txt");

  const outputDirPath = await join(dirpath, outputDirName);

  try {
    const args = [
      sanitizeArg(videoPath),
      sanitizeArg(mergedCsvPath),
      sanitizeArg(outputDirPath),
      "--log_file",
      sanitizeArg(logFile),
    ];

    // Use the sidecar binary that wraps your Python merge_labels function.
    const command = Command.sidecar("binaries/chunks", args);

    const output = await command.execute();

    // Filter out irrelevant stderr messages.
    const filteredStderr = output.stderr
      ? output.stderr
          .split("\n")
          .filter(
            (line) => !line.includes("Matplotlib is building the font cache")
          )
          .filter((line) => !line.includes("WARNING"))
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
        // { "success": true, "data": { "merged_csv": "path/to/output.csv" } }
        if (response.success && response.data && response.data.merged_csv) {
          const data: ChunksReturnedData = {
            chunksFolderPath: response.data.merged_csv,
          };

          return {
            status: "success",
            data,
          };
        } else {
          return {
            status: "error",
            data: response.message || "Chunk Videos encountered an error.",
          };
        }
      } catch (jsonError) {
        console.error("Failed to parse JSON response:", jsonError);
        return {
          status: "error",
          data: "Invalid JSON response from Chunk Videos.",
        };
      }
    }

    return {
      status: "error",
      data: "Chunk Videos completed, but no output was received.",
    };
  } catch (error) {
    return {
      status: "error",
      data: `An error occurred while running Chunk Videos: ${error}`,
    };
  }
};