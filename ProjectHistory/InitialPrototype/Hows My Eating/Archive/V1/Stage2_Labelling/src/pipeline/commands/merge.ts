import { Command } from "@tauri-apps/plugin-shell";
import { join } from "@tauri-apps/api/path";
import { sanitizeArg } from "../../utilities/commands";
import { MergeLabelsReturnedData } from "./types";

export const runMergeLabels = async (
  dirpath: string,
  labelledJsonFilePath: string,
  movInfoFilePath: string,
  mergedCsvOutputName: string
): Promise<ReturnStatus<MergeLabelsReturnedData>> => {
  console.log(
    "Running merge_labels with:",
    labelledJsonFilePath,
    movInfoFilePath,
    mergedCsvOutputName
  );

  const logFile = await join(dirpath, "merge.txt");

  try {
    // Build the argument list matching the updated CLI:
    // 1. labelled_json_filepath
    // 2. mov_info_file_path
    // 3. merged_csv_output_name
    // plus an optional "--log_file" flag.
    const args = [
      sanitizeArg(dirpath),
      sanitizeArg(labelledJsonFilePath),
      sanitizeArg(movInfoFilePath),
      sanitizeArg(mergedCsvOutputName),
      "--log_file",
      sanitizeArg(logFile),
    ];

    // Use the sidecar binary that wraps your Python merge_labels function.
    const command = Command.sidecar("binaries/merge", args);

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
      console.error("Merge Labels Error (filtered):", filteredStderr);
    }

    if (output.stdout) {
      console.log("Raw merge_labels stdout:", output.stdout);

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
          const data: MergeLabelsReturnedData = {
            merged_csv_path: response.data.merged_csv,
          };

          return {
            status: "success",
            data,
          };
        } else {
          return {
            status: "error",
            data: response.message || "Merge Labels encountered an error.",
          };
        }
      } catch (jsonError) {
        console.error("Failed to parse JSON response:", jsonError);
        return {
          status: "error",
          data: "Invalid JSON response from Merge Labels.",
        };
      }
    }

    return {
      status: "error",
      data: "Merge Labels completed, but no output was received.",
    };
  } catch (error) {
    return {
      status: "error",
      data: `An error occurred while running Merge Labels: ${error}`,
    };
  }
};