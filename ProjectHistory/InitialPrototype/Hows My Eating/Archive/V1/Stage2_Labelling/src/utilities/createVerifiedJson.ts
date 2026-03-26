import { VideoChunkStatus } from "@/types/Markers";
import { join } from "@tauri-apps/api/path";
import { writeTextFile } from "@tauri-apps/plugin-fs";

const biteOrChew = async (fileName: string): Promise<"Bite" | "Chew" | "Swallow" | "Other"> => {
  if (fileName?.startsWith("bite")) {
    return "Bite";
  } else if (fileName?.startsWith("chew")) {
    return "Chew";
  } else if (fileName?.startsWith("swallow")) {
    return "Swallow";
  } else {
    return "Other";
  }
};

const startFrame = async (fileName: string): Promise<number> => {
  // Find the string "start_frame" and set the value of start to everything after "frame" up to the next "_"
  const start = fileName.match(/start_frame(\d+)/);
  return start ? parseInt(start[1]) : -1;
};

const endFrame = async (fileName: string): Promise<number> => {
  // Find the string "end_frame" and set the value of end to everything after "frame" up to the next "_"
  const end = fileName.match(/end_frame(\d+)/);
  return end ? parseInt(end[1]) : -1;
};


export const createVerifiedJson = async (
  dataDir: string,
  videoChunks: string[],
  verifiedJsonFilePath: string
): Promise<boolean> => {
  try {
    const statusObject: JsonStatusObject = { status: "incomplete" };

    // Take each videoChunk and create a VideoChunkStatus object. Chunk represnt the entire path so the fileName = the last segment of that path
    const verifiedData: VideoChunkStatus[] = await Promise.all(
      videoChunks.map(async (chunk) => {
        const filePath = await join(dataDir, chunk);

        return {
          fileName: chunk,
          filePath,
          originalValue: await biteOrChew(chunk),
          verifiedValue: await biteOrChew(chunk),
          verified: false,
          correct: false,
          frameStart: await startFrame(chunk),
          frameEnd: await endFrame(chunk),
          relabelled: [],
        };
      })
    );

    // Join the verifiedData with the verifiedDataStatus
    const contents = JSON.stringify([statusObject, ...verifiedData]);
    await writeTextFile(verifiedJsonFilePath, contents);
    return true;
  } catch (error) {
    console.error("Error saving verified data:", error);
    return false;
  }
};
