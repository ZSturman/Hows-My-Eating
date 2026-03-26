import {
  createContext,
  useReducer,
  useContext,
  useEffect,
  useState,
} from "react";
import { open } from "@tauri-apps/api/dialog";
import {
  saveFilesToAppData,
  validateSelectedDirectory,
} from "../utils/importData";

type ImportStatus =
  | false // Import process is not running
  | "IMPORTING" // Import process is running
  | "IMPORTING_CANCELLED" // Import process was cancelled
  | "VALIDATING_DIRECTORY" // Validating the selected directory
  | "CHECKING_FILES" // Checking for the required files in the selected directory
  | "FILE_CHECK_COMPLETE" // File check process is complete
  | "MISSING_MOTION_JSON" // Required files are missing
  | "MISSING_MOV_FILE" // Required files are missing
  | "DIRECTORY_VALIDATED" // Directory has been validated
  | "GETTING_MOV_INFO" // Retrieving MOV file information
  | "MOV_INFO_COMPLETE" // MOV file information has been retrieved
  | "MOV_INFO_ERROR" // An error occurred during MOV file retrieval
  | "EXTRACTING_AUDIO" // Extracting audio from the MOV file
  | "AUDIO_EXTRACTION_COMPLETE" // Audio extraction is complete
  | "AUDIO_EXTRACTION_ERROR" // An error occurred during audio extraction
  | "GETTING_MOTION_INFO" // Getting motion data information
  | "MOTION_INFO_COMPLETE" // Motion data information has been retrieved
  | "MOTION_INFO_ERROR" // An error occurred during motion data retrieval
  | "GENERATING_CSV" // Generating CSV file from the motion data
  | "CSV_GENERATION_COMPLETE" // CSV generation is complete
  | "CSV_GENERATION_ERROR" // An error occurred during CSV generation
  | "COPYING_FILES_TO_APP_DIRECTORY" // Saving files to AppData
  | "FILES_COPIED" // Files have been copied
  | "FILE_COPY_ERROR" // An error occurred during file copying
  | "IMPORT_COMPLETE" // Import process is complete
  | "IMPORT_ERROR"; // An error occurred during the import process

const initialImportState: ImportStatus = false;

const ImportContext = createContext<{
  state: ImportStatus;
  dispatch: React.Dispatch<ImportStatus>;
  successPayload: DataRecord[];
}>({
  state: initialImportState,
  dispatch: () => null,
  successPayload: [],
});

const sessionReducer = (
  _: ImportStatus,
  action: ImportStatus
): ImportStatus => {
  switch (action) {
    case "IMPORTING":
      return "IMPORTING";

    case "IMPORTING_CANCELLED":
      return "IMPORTING_CANCELLED";

    case "VALIDATING_DIRECTORY":
      return "VALIDATING_DIRECTORY";

    case "MISSING_MOTION_JSON":
      return "MISSING_MOTION_JSON";

    case "MISSING_MOV_FILE":
      return "MISSING_MOV_FILE";

    case "DIRECTORY_VALIDATED":
      return "DIRECTORY_VALIDATED";

    case "GETTING_MOV_INFO":
      return "GETTING_MOV_INFO";

    case "MOV_INFO_COMPLETE":
      return "MOV_INFO_COMPLETE";

    case "MOV_INFO_ERROR":
      return "MOV_INFO_ERROR";

    case "EXTRACTING_AUDIO":
      return "EXTRACTING_AUDIO";

    case "AUDIO_EXTRACTION_COMPLETE":
      return "AUDIO_EXTRACTION_COMPLETE";

    case "AUDIO_EXTRACTION_ERROR":
      return "AUDIO_EXTRACTION_ERROR";

    case "GETTING_MOTION_INFO":
      return "GETTING_MOTION_INFO";

    case "MOTION_INFO_COMPLETE":
      return "MOTION_INFO_COMPLETE";

    case "MOTION_INFO_ERROR":
      return "MOTION_INFO_ERROR";

    case "GENERATING_CSV":
      return "GENERATING_CSV";

    case "CSV_GENERATION_COMPLETE":
      return "CSV_GENERATION_COMPLETE";

    case "CSV_GENERATION_ERROR":
      return "CSV_GENERATION_ERROR";

    case "COPYING_FILES_TO_APP_DIRECTORY":
      return "COPYING_FILES_TO_APP_DIRECTORY";

    case "FILES_COPIED":
      return "FILES_COPIED";

    case "FILE_COPY_ERROR":
      return "FILE_COPY_ERROR";

    case "IMPORT_COMPLETE":
      return "IMPORT_COMPLETE";

    case "IMPORT_ERROR":
      return "IMPORT_ERROR";

    default:
      return false;
  }
};

export const ImportProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [state, dispatch] = useReducer(sessionReducer, initialImportState);
  const [nextState, setNextState] = useState<ImportStatus>(false);
  const [importDirectory, setImportDirectory] = useState<
    string | string[] | null
  >(null);
  const [successPayload, setSuccessPayload] = useState<DataRecord[]>([]);
  const [errorPayload, setErrorPayload] = useState<string[]>([]);

  useEffect(() => {
    if (nextState === "IMPORTING_CANCELLED") {
      setImportDirectory(null);
      dispatch("IMPORTING_CANCELLED");
    } else if (nextState === "IMPORT_COMPLETE") {
      dispatch("IMPORT_COMPLETE");
    } else if (nextState === "VALIDATING_DIRECTORY") {
      dispatch("VALIDATING_DIRECTORY");
    } 
  }, [nextState]);

  useEffect(() => {
    const importDataRecord = async () => {
      try {
        const selected = await open({
          directory: true,
          multiple: true,
        });
        setImportDirectory(selected);
        setNextState("VALIDATING_DIRECTORY");
      } catch (error) {
        console.log("ERROR: ", error);
        setNextState("IMPORTING_CANCELLED");
      }
    };

    const validateImportDirectory = async () => {
      if (Array.isArray(importDirectory)) {
        for (const dir of importDirectory) {
          const directoryValidated = await validateSelectedDirectory(dir);
          if (directoryValidated.status === "SUCCESS") {
            const dataSaved = await saveFilesToAppData(dir);
            if (dataSaved.status === "SUCCESS") {
              setSuccessPayload([...successPayload, dataSaved.payload]);
              setNextState("IMPORT_COMPLETE");
            } else {
              /* setNextState(MISSING_MOTION_JSON)... */
              setNextState("IMPORTING_CANCELLED");
              setErrorPayload([...errorPayload, dataSaved.message]);
            }
          }
        }
      } else if (importDirectory === null) {
        setNextState("IMPORTING_CANCELLED");
      } else {
        const validated = await validateSelectedDirectory(importDirectory);
        if (validated.status === "SUCCESS") {
          const dataSaved = await saveFilesToAppData(importDirectory);
          if (dataSaved.status === "SUCCESS") {
            setSuccessPayload([...successPayload, dataSaved.payload]);
            setNextState("IMPORT_COMPLETE");
          } else {
            setNextState("IMPORTING_CANCELLED");
            setErrorPayload([...errorPayload, dataSaved.message]);
          }
        }
      }
    };

    if (state === "IMPORTING") {
      importDataRecord();
    } else if (state === "VALIDATING_DIRECTORY" && importDirectory) {
      validateImportDirectory();
    }
  }, [state, importDirectory]);

  return (
    <ImportContext.Provider value={{ state, dispatch, successPayload }}>
      {children}
    </ImportContext.Provider>
  );
};

export const useImportContext = () => useContext(ImportContext);
