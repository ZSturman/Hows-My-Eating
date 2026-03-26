import { handleExportData } from "../../utilities/handleExportData";

// Mock the filesystem functions to force a failure case
jest.mock("@tauri-apps/plugin-fs", () => ({
  exists: async () => false, // force non-existing path
  readDir: async () => [],
  mkdir: async () => {},
  copyFile: async () => {},
  readTextFile: async () => "",
}));
jest.mock("@tauri-apps/api/path", () => ({
  join: (...args: any[]) => args.join("/"),
}));
jest.mock("../Stage2_Labelling/src/utilities/directoryChecks", () => ({
  isDirectory: async () => true,
}));

describe("handleExportData", () => {
  it("should return error if dataPath does not exist", async () => {
    const appConfig = {} as any;
    const result = await handleExportData("/fake/data", "/fake/data", appConfig);
    expect(result.success).toBe(false);
  });
});
