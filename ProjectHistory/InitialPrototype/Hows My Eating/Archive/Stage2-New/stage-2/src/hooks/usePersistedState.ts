import { useEffect, useState } from "react";
import {
  importAppRecordFromFile,
} from "../handlers/appRecordFileHandler";
import { AppRecord } from "../context/AppRecordContext";

const usePersistedState = () => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [appRecord, setAppState] = useState<AppRecord | null>(null);

  useEffect(() => {
    const loadRecords = async () => {
      console.log("Loading state...");
      try {
        const fileRecords = await importAppRecordFromFile();
        if (fileRecords) {
          setAppState(fileRecords);
        }
      } catch (error) {
        console.error("Error loading state from file:", error);
      } finally {
        setIsLoaded(true);
      }
    };

    loadRecords();
  }, []);



  return { appRecord, isLoaded };
};

export default usePersistedState;
