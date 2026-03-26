import { isValidState } from "../../utilities/isValid";

describe("isValidState", () => {
  it("should return true for valid non-null, non-loading and non-error values", () => {
    expect(isValidState(123)).toBe(true);
    expect(isValidState("ok")).toBe(true);
  });
  it("should return false for invalid states", () => {
    expect(isValidState(null)).toBe(false);
    expect(isValidState("loading")).toBe(false);
    expect(isValidState("error")).toBe(false);
  });
});
