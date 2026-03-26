import copyFilesToAppDataDir from "../../utilities/copyFiles";
import { exists, mkdir, copyFile } from "@tauri-apps/plugin-fs";
import { join } from "@tauri-apps/api/path";

jest.mock("@tauri-apps/plugin-fs", () => ({
  exists: jest.fn().mockResolvedValue(false),
  mkdir: jest.fn().mockResolvedValue(undefined),
  copyFile: jest.fn().mockResolvedValue(undefined),
}));
jest.mock("@tauri-apps/api/path", () => ({
  join: (...args: any[]) => args.join("/"),
}));

describe("copyFilesToAppDataDir", () => {
  it("should return error if data directory is not valid", async () => {
    const result = await copyFilesToAppDataDir(
      "/sourceDir",
      "file.json",
      "video.mov",
      "", // invalid dataDirectory
      "importedFolder"
    );
    expect(result.status).toBe("error");
  });
});
