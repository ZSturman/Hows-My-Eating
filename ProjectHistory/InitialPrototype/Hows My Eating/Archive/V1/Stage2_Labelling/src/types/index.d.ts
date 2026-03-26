// Defines the loading state used across the app.
type LoadingState = "loading" | "error" | null;

// Log entry structure used for system logging.
type LogEntry = {
  timestamp: number;
  type: "INFO" | "WARNING" | "ERROR" | "SUCCESS";
  message: string;
  action?: string;
}

type ReturnStatus<T = unknown> =
  | { status: "success"; data: T }
  | { status: "error"; data: string };

  type AppConfig = {
    outputProcessedVideo: boolean
    requireMainVideoThumbnail: boolean
    requireScrubbingThumbnails: boolean

    importFolderName: string
    archiveFolderName: string
    labelledJsonStartsWithString: string
    importedDataParentFolderName: string
    mergedCsvFileName: string
    chunksDirectoryName: string
    verifiedJsonStartsWithString: string
    exportFolderName: string
    movInfoFileName: string
    processVisualsCsvFileName: string
    compareVisualsCsvFileName: string
  }

type JsonStatusObject = {
  status: "complete"
} | {
  status: "incomplete"
} | {
  status: "error"
  errors: string[]
}