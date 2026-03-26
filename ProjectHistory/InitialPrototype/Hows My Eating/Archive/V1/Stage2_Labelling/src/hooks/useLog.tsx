import { useState, useEffect } from "react";

/** Log entry interface */
interface LogEntry {
  timestamp: number;
  type: "SUCCESS" | "ERROR" | "INFO" | "WARNING";
  message: string;
  stackTrace?: string; // Optional stack trace information
}

/**
 * useLog
 *
 * @description Provides functions for logging success, error, info, and warning messages.
 * Stores logs in a local state to be used for debugging or UI display.
 *
 * @returns- Logging functions and logs array.
 */
export const useLog = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [toastBackLog, setToastBackLog] = useState<LogEntry[]>([]);
  const [toastMessage, setToastMessage] = useState<LogEntry | null>(null);

  useEffect(() => {
    if (toastBackLog.length === 0) {
      setToastMessage(null);
      return;
    }
    setToastMessage(toastBackLog[0]);
  }, [toastBackLog]);

  useEffect(() => {
    if (toastMessage === null) {
      return;
    }
    const timeout = setTimeout(() => {
      setToastBackLog((prev) => prev.slice(1));
    }, 5000);

    return () => clearTimeout(timeout);
  }, [toastMessage]);

  /** Captures stack trace and formats it */
  const getStackTrace = (): string => {
    const error = new Error();
    const stackLines = error.stack?.split("\n") || [];
    // Filter out the first two lines (Error message + this function call)
    return stackLines.slice(2).join("\n");
  };

  /** Adds a log entry with stack trace */
  const addLog = (entry: LogEntry, addToToast: boolean = false) => {
    setLogs((prevLogs) => [...prevLogs, entry]);
    if (addToToast) {
      setToastBackLog((prev) => [...prev, entry]);
    }
  };

  /** Logs a success message */
  const addSuccess = (message: string, addToToast: boolean = false) => {
    const stackTrace = getStackTrace();
    addLog({ timestamp: Date.now(), type: "SUCCESS", message, stackTrace }, addToToast);
    console.log(`✅ SUCCESS: ${message}\n${stackTrace}`);
  };

  /** Logs an error message */
  const addError = (message: string, addToToast: boolean = false) => {
    const stackTrace = getStackTrace();
    addLog({ timestamp: Date.now(), type: "ERROR", message, stackTrace }, addToToast);
    console.error(`❌ ERROR: ${message}\n${stackTrace}`);
  };

  /** Logs an informational message */
  const addInfo = (message: string, addToToast: boolean = false) => {
    const stackTrace = getStackTrace();
    addLog({ timestamp: Date.now(), type: "INFO", message, stackTrace }, addToToast);
    console.info(`ℹ️ INFO: ${message}\n${stackTrace}`);
  };

  /** Logs a warning message */
  const addWarning = (message: string, addToToast: boolean = false) => {
    const stackTrace = getStackTrace();
    addLog({ timestamp: Date.now(), type: "WARNING", message, stackTrace }, addToToast);
    console.warn(`⚠️ WARNING: ${message}\n${stackTrace}`);
  };

  /** Clears the logs */
  const clearLogs = () => {
    setLogs([]);
  };

  return {
    logs,
    addSuccess,
    addError,
    addInfo,
    addWarning,
    clearLogs,
    toastMessage,
  };
};