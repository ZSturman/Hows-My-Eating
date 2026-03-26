/**
 * Adds a log message and optionally updates a state setter function.
 * @param newMessage - The new log entry to be added.
 * @param setMessage - Optional function to update the message state.
 */
export const addLogMessage = async (
  newMessage: Readonly<LogEntry>,
  setMessage?: (message: LogEntry) => void
): Promise<void> => {
  const timestamp = new Date(newMessage.timestamp).toISOString();

  // Structured log entry for better debugging.
  const logEntry = {
    timestamp,
    level: newMessage.type, // "INFO", "WARNING", "ERROR", "SUCCESS"
    message: newMessage.message,
  };

  // Print to console based on log level
  const formattedLog = JSON.stringify(logEntry, null, 2);
  switch (newMessage.type) {
    case "ERROR":
      console.error(formattedLog);
      break;
    case "WARNING":
      console.warn(formattedLog);
      break;
    case "INFO":
      console.info(formattedLog);
      break;
    default:
      console.log(formattedLog);
      break;
  }

  // Update state if setter function is provided
  setMessage?.(newMessage);
};
