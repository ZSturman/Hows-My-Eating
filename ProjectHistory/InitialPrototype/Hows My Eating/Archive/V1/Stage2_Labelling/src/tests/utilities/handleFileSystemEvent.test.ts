import { handleFileSystemEvent } from "../../utilities/handleFileSystemEvent";

describe("handleFileSystemEvent", () => {
  it("should log when a JSON file is created", async () => {
    const logSpy = jest.spyOn(console, "log").mockImplementation(() => {});
    const event = {
      type: { create: { kind: "file" } },
      paths: ["/some/path/file.json"],
    };
    await handleFileSystemEvent(event);
    expect(logSpy).toHaveBeenCalledWith(expect.stringContaining("New file created:"), true);
    expect(logSpy).toHaveBeenCalledWith(expect.stringContaining("JSON file detected:"), true);
    logSpy.mockRestore();
  });
});
