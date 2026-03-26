import { createVerifiedJson } from "../../utilities/createVerifiedJson";
import { writeTextFile } from "@tauri-apps/plugin-fs";

jest.mock("@tauri-apps/plugin-fs", () => ({
  writeTextFile: jest.fn().mockResolvedValue(undefined),
}));
jest.mock("@tauri-apps/api/path", () => ({
  join: (...args: any[]) => args.join("/"),
}));

describe("createVerifiedJson", () => {
  it("should successfully write verified json content", async () => {
    const result = await createVerifiedJson("/data", ["chunk1.json"], "/data/verified.json");
    expect(result).toBe(true);
    expect(writeTextFile).toHaveBeenCalled();
  });
});
