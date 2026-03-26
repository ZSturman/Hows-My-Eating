import { hasJson, hasMov } from "../../utilities/directoryChecks";

describe("directoryChecks", () => {
  const fakeEntries = [
    { name: "data.json" },
    { name: "video.mov" },
    { name: "notes.txt" },
  ] as any;

  it("hasJson should return the json file", async () => {
    const jsonEntry = await hasJson(fakeEntries);
    expect(jsonEntry).toBe("data.json");
  });

  it("hasMov should return the mov file", async () => {
    const movEntry = await hasMov(fakeEntries);
    expect(movEntry).toBe("video.mov");
  });
});
