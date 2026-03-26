import { Command } from "@tauri-apps/plugin-shell";
import { join } from "@tauri-apps/api/path";
import { sanitizeArg } from "../../utilities/commands";
import { ComputeRatiosReturnedData } from "./types";

export const runComputeRatios = async (
  dirpath: string,
  points_data_csv_path: string,
  compareVisualsCsvFileName: string
): Promise<ReturnStatus<ComputeRatiosReturnedData>> => {
  const logFile = await join(dirpath, `${compareVisualsCsvFileName}.log`);

  try {
    let args = [
      sanitizeArg(points_data_csv_path),
      sanitizeArg(compareVisualsCsvFileName),
      "--log_file",
      sanitizeArg(logFile),
    ];

    const command = Command.sidecar("binaries/compute-ratios", args);
    const output = await command.execute();

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
      console.error("Compute Ratios Error (filtered):", filteredStderr);
    }

    if (output.stdout) {
      console.log("Raw Compute Ratios stdout:", output.stdout);

      try {
        const startIndex = output.stdout.indexOf('{"success":');
        if (startIndex === -1) {
          throw new Error("No valid JSON response found in the output.");
        }

        const jsonResponseString = output.stdout.slice(startIndex);
        const response = JSON.parse(jsonResponseString);

        // **Ensure failure is properly detected**
        if (!response.success) {
          console.error("Step 1C failed with message:", response.message);
          return {
            status: "error",
            data:
              response.message ||
              "Compute Ratios encountered an unknown error.",
          };
        }

        // **Only return success if response.success is true**
        return {
          status: "success",
          data: {
            csv_file_path: response.data?.csv_file || "",
          },
        };
      } catch (jsonError) {
        console.error("Failed to parse JSON response:", jsonError);
        return {
          status: "error",
          data: "Invalid JSON response from Compute Ratios.",
        };
      }
    }

    return {
      status: "error",
      data: "Compute Ratios completed, but no valid output was received.",
    };
  } catch (error) {
    return {
      status: "error",
      data: `An error occurred while running Compute Ratios: ${error}`,
    };
  }
};
