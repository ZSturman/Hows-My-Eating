import { Command } from "@tauri-apps/plugin-shell";
import { join } from "@tauri-apps/api/path";
import { sanitizeArg } from "../../utilities/commands";

export const runNoChew = async (
    dataPath: string,
    outputDataPath: string,
): Promise<boolean> => {
  console.log(
    "Running no_chew with", 
    dataPath,
    outputDataPath
  );

  const logFile = await join(dataPath, "noChew.log");

  try {
    const args = [
        sanitizeArg(dataPath),
        sanitizeArg(outputDataPath),
      "--log_file",
      sanitizeArg(logFile),
    ];

    // Use the sidecar binary that wraps your Python merge_labels function.
    const command = Command.sidecar("binaries/not_chew", args);

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