import { Command } from "@tauri-apps/plugin-shell";
import { join } from "@tauri-apps/api/path";
import { sanitizeArg } from "../../utilities/commands";
import { ProcessVisualsReturnedData } from "./types";




export const runProcessVisuals = async (
  dirpath: string,
  processVisualsCsvFileName: string,
  outputVideo: string
): Promise<ReturnStatus<ProcessVisualsReturnedData>> => {
  console.log("Running Process Visuals with dirpath:", dirpath);

  const logFile = await join(dirpath, "process-visuals.log");

  if (outputVideo !== "True" && outputVideo !== "False") {
    return {
      status: "error",
      data: "Invalid outputVideo parameter. Must be 'True' or 'False'.",
    };
  }

  try {
    let args = [
      sanitizeArg(dirpath),
      sanitizeArg(processVisualsCsvFileName),
      "--log_file",
      sanitizeArg(logFile),
      "--output-video",
      outputVideo,
    ];

    console.log("Process Visuals args:", JSON.stringify(args));

    const command = Command.sidecar("binaries/process-visuals", args);

    const output = await command.execute();

    // Handle stderr filtering (ignoring irrelevant warnings)
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
      console.error("Process Visuals Error (filtered):", filteredStderr);
    }

    if (output.stdout) {
      console.log("Raw Process Visuals stdout:", output.stdout);

      try {
        // Extract JSON starting from the desired part
        const startIndex = output.stdout.indexOf('{"success":');
        if (startIndex === -1) {
          throw new Error("No valid JSON response found in the output.");
        }

        const jsonResponseString = output.stdout.slice(startIndex);

        // Parse JSON response from Python
        const response = JSON.parse(jsonResponseString);

        if (response.success && response.data) {
          const status = "success";

          const data = {
            csv_file_path: response.data?.csv_file || "",
            video_file_path: response.data?.video_file || null,
          };

          return {
            status,
            data,
          };
        } else {
          return {
            status: "error",
            data: response.message || "Process Visuals encountered an error.",
          };
        }
      } catch (jsonError) {
        console.error("Failed to parse JSON response:", jsonError);
        return {
          status: "error",
          data: "Invalid JSON response from Process Visuals.",
        };
      }
    }

    return {
      status: "error",
      data: "Process Visuals completed, but no output was received.",
    };
  } catch (error) {
    return {
      status: "error",
      data: `An error occurred while running Process Visuals: ${error}`,
    };
  }
};
