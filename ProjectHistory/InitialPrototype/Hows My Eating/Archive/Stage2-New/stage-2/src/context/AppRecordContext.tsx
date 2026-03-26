import React, {
  createContext,
  useReducer,
  useContext,
  ReactNode,
  Dispatch,
  useEffect,
} from "react";
import usePersistedState from "../hooks/usePersistedState";
import {
  exportAppRecordToFile,
} from "../handlers/appRecordFileHandler";

import { resourceDir } from "@tauri-apps/api/path";
import { initialAppRecord } from "../defaults/initialAppState";

export type AppRecord = {
  sessions: number[]; // Array of session timestamps
  lastModified: number; // Timestamp of the last time the app was modified
  dataDirectories: DataRecord[];
};

type AppRecordState = AppRecord & {
  outOfDate: boolean;
  addSessionDate: boolean;
};

type AppRecordAction =
  | { type: "UPDATE_SESSIONS" }
  | { type: "APP_RECORD_OUTDATED" }
  | { type: "UPDATING_APP_RECORD"; payload: Partial<AppRecord> }
  | { type: "APP_UP_TO_DATE" }
  | { type: "SET_APP_RECORD"; payload: AppRecord }
  | { type: "ADD_DATA_RECORD"; payload: DataRecord[] };

// Init Actions
const appReducer = (
  state: AppRecordState,
  action: AppRecordAction
): AppRecordState => {
  console.log("Reducer action received:", action);
  switch (action.type) {
    case "UPDATE_SESSIONS":
      return {
        ...state,
        sessions: [...state.sessions, Date.now()],
        outOfDate: true,
      };
    case "APP_RECORD_OUTDATED":
      return {
        ...state,
        outOfDate: true,
      };

      case "ADD_DATA_RECORD": 
      return {
        ...state,
        dataDirectories: [...state.dataDirectories, ...action.payload],
        outOfDate: true,
      }

    case "APP_UP_TO_DATE":
      return state;

    case "SET_APP_RECORD":
      return {
        ...state,
        ...action.payload,
      };

    case "UPDATING_APP_RECORD":
      console.log("Updating app record");
      return {
        ...state,
        lastModified: Date.now(),
        ...action.payload,
      };
    default:
      return state;
  }
};

// Context for App Records and Session State
const AppRecordContext = createContext<{
  state: AppRecord;
  dispatch: Dispatch<AppRecordAction>;
}>({
  state: initialAppRecord,
  dispatch: () => undefined,
});

// Provider Component
export const AppRecordProvider: React.FC<{
  children: ReactNode;
}> = ({ children }) => {

  const { appRecord, isLoaded } = usePersistedState()

  const [state, dispatch] = useReducer(
    appReducer,
    {
      ...initialAppRecord,
      outOfDate: false,
      addSessionDate: false,
    }
  );

  useEffect(() => {

    if (isLoaded && appRecord) {
      console.log("App Record loaded from file: ", appRecord);
      dispatch({ type: "SET_APP_RECORD", payload: {...appRecord} });
      
    }

  }, [isLoaded])

  useEffect(() => {
    const getPaths = async () => {
      const resourceDirPath = await resourceDir();
      console.log("Resource Dir Path: ", resourceDirPath);
    };
    getPaths();
  }, []);

  useEffect(() => {
    const syncStateToFile = async () => {
      let saveTimeout: NodeJS.Timeout | null = null;

      // Debounce the save operation
      if (saveTimeout) {
        clearTimeout(saveTimeout);
      }
      saveTimeout = setTimeout(async () => {
        const appRecordToUpdate: AppRecord = {
          sessions: state.sessions,
          lastModified: state.lastModified,
          dataDirectories: state.dataDirectories,
        };
        await exportAppRecordToFile(appRecordToUpdate);
        console.log("State saved to file successfully");
        dispatch({ type: "APP_UP_TO_DATE" });
      }, 5000);
    };

    if (state.outOfDate) {
      syncStateToFile();
    }
  }, [state.outOfDate]);


  return (
    <AppRecordContext.Provider
      value={{
        state,
        dispatch,
      }}
    >
      {children}
    </AppRecordContext.Provider>
  );
};

// Custom Hook to use the AppState
export const useAppRecord = () => useContext(AppRecordContext);
