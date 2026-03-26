import importData from "../../utilities/importData";

// Mock dependencies to simulate error condition for simplicity
jest.mock("../Stage2_Labelling/src/utilities/directoryChecks", () => ({
  isDirectory: async () => false, // force error by not being a directory
  hasJson: async () => false,
  hasMov: async () => false,
}));
  
describe("importData", () => {
  it("should return error if path is not a directory", async () => {
    const result = await importData("/fake/path", "/data", "importedFolder");
    expect(result.status).toBe("error");
  });
});
