import { Command } from "@tauri-apps/plugin-shell";
import { join } from "@tauri-apps/api/path";
import {
  filterStderr,
  parseJsonResponse,
  sanitizeArg,
} from "../../utilities/commands";
import { CollectMovInfoReturnedData } from "./types";

export const runCollectMovInfo = async (
  dirpath: string,
  movInfoFileName: string
): Promise<ReturnStatus<CollectMovInfoReturnedData>> => {
  console.log("Running Collect Mov Info with dirpath:", dirpath);

  const logFile = await join(dirpath, "collect-mov-info.txt");

  try {
    const command = Command.sidecar("binaries/collect-mov-info", [
      sanitizeArg(dirpath),
      sanitizeArg(movInfoFileName),
      "--log_file",
      sanitizeArg(logFile),
    ]);

    const output = await command.execute();

    const filteredStderr = filterStderr(output.stderr);

    if (filteredStderr) {
      console.log("Collect Mov Info Error (filtered):", filteredStderr);
    }

    if (output.stdout) {
      console.log("Raw Collect Mov Info stdout:", output.stdout);
      return parseJsonResponse<CollectMovInfoReturnedData>(output.stdout);
    }

    return {
      status: "error",
      data: "Collect Mov Info completed, but no output was received.",
    };
  } catch (error) {
    return {
      status: "error",
      data: `An error occurred while running Collect Mov Info: ${error}`,
    };
  }
};
