import { jsonFileHasContent, csvFileHasContent, fileHasContent } from "../../utilities/fileChecks";
import { exists, readTextFile, stat } from "@tauri-apps/plugin-fs";

jest.mock("@tauri-apps/plugin-fs");

describe("fileChecks", () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });
  
  it("jsonFileHasContent should return false for empty content", async () => {
    (exists as jest.Mock).mockResolvedValue(true);
    (readTextFile as jest.Mock).mockResolvedValue("   ");
    const result = await jsonFileHasContent("/fake/file.json");
    expect(result).toBe(false);
  });

  it("csvFileHasContent should return false if only header exists", async () => {
    (exists as jest.Mock).mockResolvedValue(true);
    (readTextFile as jest.Mock).mockResolvedValue("header\n");
    const result = await csvFileHasContent("/fake/file.csv");
    expect(result).toBe(false);
  });

  it("fileHasContent should check based on extension", async () => {
    (exists as jest.Mock).mockResolvedValue(true);
    (stat as jest.Mock).mockResolvedValue({ size: 100 });
    (readTextFile as jest.Mock).mockResolvedValue('{"key": "value"}');
    const result = await fileHasContent("/fake/file.json");
    expect(result).toBe(true);
  });
});
