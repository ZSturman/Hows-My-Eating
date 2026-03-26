import appendDataToJson from "../../utilities/appendDataToJson";
import { readTextFile, writeTextFile } from "@tauri-apps/plugin-fs";

jest.mock("@tauri-apps/plugin-fs", () => ({
  readTextFile: jest.fn(),
  writeTextFile: jest.fn().mockResolvedValue(undefined),
}));

describe("appendDataToJson", () => {
  beforeEach(() => {
    (readTextFile as jest.Mock).mockReset();
  });

  it("should create a new JSON array if file is empty/malformed", async () => {
    (readTextFile as jest.Mock).mockRejectedValue(new Error("file error"));
    const newData = { id: "123", imported: true } as any;
    const result = await appendDataToJson("/fake/file.json", newData);
    expect(result).toBe(true);
    expect(writeTextFile).toHaveBeenCalled();
  });

  it("should append new data if file contains a JSON array", async () => {
    (readTextFile as jest.Mock).mockResolvedValue("[]");
    const newData = { id: "456", imported: false } as any;
    const result = await appendDataToJson("/fake/file.json", newData);
    expect(result).toBe(true);
    expect(writeTextFile).toHaveBeenCalled();
  });
});
