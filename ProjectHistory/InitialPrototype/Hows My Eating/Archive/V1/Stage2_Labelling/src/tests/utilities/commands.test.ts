import { sanitizeArg, filterStderr, parseJsonResponse } from "../../utilities/commands";

describe("commands", () => {
  it("sanitizeArg should remove unsafe characters", () => {
    const unsafe = `hello"'$\\\``;
    const safe = sanitizeArg(unsafe);
    expect(safe).not.toMatch(/["'\\$`]/);
  });

  it("filterStderr should filter out lines", () => {
    const input = "Message\nMatplotlib is building the font cache\nWARNING: test";
    const output = filterStderr(input);
    expect(output).not.toMatch(/Matplotlib/);
    expect(output).not.toMatch(/WARNING/);
    expect(output).toMatch(/Message/);
  });

  it("parseJsonResponse should parse valid JSON response", () => {
    const jsonResponse = JSON.stringify({ success: true, data: { key: "value" } });
    const stdout = "log info\n" + jsonResponse;
    const result = parseJsonResponse(stdout);
    expect(result.status).toBe("success");
    expect(result.data).toEqual({ key: "value" });
  });
});
