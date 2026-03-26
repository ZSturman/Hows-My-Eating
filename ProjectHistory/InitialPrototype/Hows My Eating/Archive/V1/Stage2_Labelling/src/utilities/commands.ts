const linesToFilter = [
  "Matplotlib is building the font cache",
  "WARNING",
]

// Sanitize arguments to prevent special characters issues
export const sanitizeArg = (arg: string): string => {
  return arg.replace(/["'\\$`]/g, ""); // Removes potentially unsafe characters
};

export const filterStderr = (stderr: string | undefined): string => {
  if (!stderr) return "";
  return stderr
    .split("\n")
    .filter((line) => !linesToFilter.some((filter) => line.includes(filter)))
    .join("\n");
};

export const parseJsonResponse = <T>(stdout: string): ReturnStatus<T> => {
  try {
    const startIndex = stdout.indexOf('{"success":');
    if (startIndex === -1) {
      throw new Error("No valid JSON response found in the output.");
    }

    const jsonResponseString = stdout.slice(startIndex);
    const response = JSON.parse(jsonResponseString);

    if (response.success && response.data) {
      return {
        status: "success",
        data: response.data as T,
      };
    } else {
      return {
        status: "error",
        data: response.message || "Command encountered an error.",
      };
    }
  } catch (error) {
    console.error("Failed to parse JSON response:", error);
    return {
      status: "error",
      data: "Invalid JSON response from Command.",
    };
  }
};