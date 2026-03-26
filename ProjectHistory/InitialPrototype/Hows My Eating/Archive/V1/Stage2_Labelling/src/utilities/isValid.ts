/**
 * Checks whether a value is valid (not `null`, `"loading"`, or `"error"`).
 * 
 * @param value - The value to evaluate.
 * @returns `true` if the value is valid, otherwise `false`.
 */
export const isValidState = <T>(value: T | LoadingState): value is T => {
  return value !== null && value !== "loading" && value !== "error";
};