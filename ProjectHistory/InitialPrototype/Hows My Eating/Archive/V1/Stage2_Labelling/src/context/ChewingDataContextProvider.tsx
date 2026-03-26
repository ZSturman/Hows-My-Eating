import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import { isValidState } from "../utilities/isValid";
import { join } from "@tauri-apps/api/path";
import {
  create,
  DirEntry,
  exists,
  readDir,
  readTextFile,
  remove,
} from "@tauri-apps/plugin-fs";

import { open } from "@tauri-apps/plugin-dialog";
import { useLog } from "../hooks/useLog";
import { useAppContext } from "./AppContext";
import { watch } from "@tauri-apps/plugin-fs";
import { processTaskPipeline } from "../pipeline/taskProcessor";
import importData from "../utilities/importData";
import { handleExportData } from "../utilities/handleExportData";
import { runNoChew } from "../pipeline/commands/runNoChew";
import { Marker } from "@/types/Markers";
import moveFolderToArchived from "../utilities/moveFolderToArchived";

type TaskQueue = {
  enqueued: string[];
  completed: string[];
  waiting: string[];
  errored: string[];
};

const defaultTaskQueue: TaskQueue = {
  enqueued: [],
  completed: [],
  waiting: [],
  errored: [],
};

// Create the shape of our Context
type ChewingDataContextType = {
  fileSystemUpdate: Date;
  handleImport: (forLabelling: boolean, path: string) => void;
  imports: string[];
  archived: string[];
  taskQueue: TaskQueue;
  exportData: (data: string) => void;
  selectedData: string | null;
  setSelectedData: (data: string | null) => void;
  refreshData: () => void;
  processing: boolean;
  redoLabels: (path: string) => void;
  moveToArchiveFolder: (path: string) => void;
  selectedArchivedData: string | null;
  setSelectedArchivedData: (data: string | null) => void;
  deleteData: (path: string) => void;
};

// Default context value
const defaultChewingDataContext: ChewingDataContextType = {
  fileSystemUpdate: new Date(),
  handleImport: () => {},
  imports: [],
  archived: [],
  taskQueue: defaultTaskQueue,
  exportData: () => {},
  selectedData: null,
  setSelectedData: () => {},
  refreshData: () => {},
  processing: false,
  redoLabels: () => {},
  moveToArchiveFolder: () => {},
  selectedArchivedData: null,
  setSelectedArchivedData: () => {},
  deleteData: () => {},
};

// Create Context
const ChewingDataContext = createContext<ChewingDataContextType>(
  defaultChewingDataContext
);

// Provider Component
export const ChewingDataContextProvider = ({
  children,
}: {
  children: ReactNode;
}) => {
  const { dataDirectory, appConfig } = useAppContext();
  const { addError, addInfo, addSuccess } = useLog();
  const [selectedData, setSelectedData] = useState<string | null>(null);
  const [imports, setImports] = useState<string[]>([]);
  const [taskQueue, setTaskQueue] = useState<TaskQueue>(defaultTaskQueue);
  const [fileSystemUpdate, setFileSystemUpdate] = useState<Date>(new Date());
  const [processing, setProcessing] = useState(false);
  const [archived, setArchived] = useState<string[]>([]);
  const [selectedArchivedData, setSelectedArchivedData] = useState<
    string | null
  >(null);

  useEffect(() => {
    maybeProcessNextTask();
  }, [taskQueue.enqueued]);

  useEffect(() => {
    fetchData(true);
  }, [dataDirectory, appConfig]);

  const fetchData = async (updateTaskQueue: boolean) => {
    if (!isValidState(dataDirectory) || !isValidState(appConfig)) return;
    try {
      const importParentDir = await join(
        dataDirectory,
        appConfig.importedDataParentFolderName
      );

      // Check if the directory exists
      const directoryExists = await exists(importParentDir);
      if (!directoryExists) {
        setImports([]);
        addSuccess("No tracked data found", true);
        return;
      } else {
        // Check for directories in the importParentDir
        const enteries: DirEntry[] = await readDir(importParentDir);

        // Check that each entry in enteries is a Directory not a file
        const data: string[] = enteries
          .filter((entry) => entry.isDirectory)
          .map((entry) => entry.name);

        const fullPaths = await Promise.all(
          data.map(async (entry) => await join(importParentDir, entry))
        );
        setImports(fullPaths);

        if (updateTaskQueue) {
          setTaskQueue({
            enqueued: fullPaths,
            completed: [],
            waiting: [],
            errored: [],
          });
        }
      }

      const archiveFolder = appConfig.archiveFolderName || "archived";

      const archiveParentDir = await join(dataDirectory, archiveFolder);

      // Check if the directory exists
      const archiveDirectoryExists = await exists(archiveParentDir);
      if (!archiveDirectoryExists) {
        setArchived([]);
        addSuccess("No tracked data found", true);
        return;
      } else {
        // Check for directories in the importParentDir
        const enteries: DirEntry[] = await readDir(archiveParentDir);

        // Check that each entry in enteries is a Directory not a file
        const data: string[] = enteries
          .filter((entry) => entry.isDirectory)
          .map((entry) => entry.name);

        const fullPaths = await Promise.all(
          data.map(async (entry) => await join(archiveParentDir, entry))
        );
        setArchived(fullPaths);
      }
    } catch (error) {
      addError("Error loading tracked data", true);
    }
  };

  const refreshData = async () => {
    fetchData(true);
  };

  const handleAddData = async (path: string) => {
    if (!isValidState(dataDirectory)) {
      addError("Data directory not found", true);
      return;
    }
    const importedFolderName =
      appConfig.importedDataParentFolderName || "imported";
    const { status, data } = await importData(
      path,
      dataDirectory,
      importedFolderName
    );
    if (status === "error") {
      addError(data, true);
      return;
    }
    taskQueue.enqueued.push(data);
    maybeProcessNextTask();

    if (!isValidState(imports)) {
      return;
    }
    setImports([...imports, data]);
  };

  useEffect(() => {
    if (!isValidState(dataDirectory) || !isValidState(appConfig)) {
      console.log("Invalid state for watcher");
      return;
    }

    let unwatchFn: (() => void) | null = null;

    const initializeWatchers = async () => {
      try {
        unwatchFn = await watch(
          dataDirectory,
          async (event) => {
            setFileSystemUpdate(new Date());

            if (typeof event.type === "object") {
              if ("remove" in event.type) {
                const removeType = event.type.remove; // This is WatchEventKindRemove
                if (removeType.kind === "folder") {
                  console.log(`Folder removed: ${event.paths}`);

                  // Now safely remove paths from imports & archived
                  event.paths.forEach((removedPath) => {
                    setImports((prevImports) =>
                      prevImports.filter((imported) => imported !== removedPath)
                    );
                    setArchived((prevArchived) =>
                      prevArchived.filter(
                        (archived) => archived !== removedPath
                      )
                    );
                    addInfo(`Folder removed: ${removedPath}`, true);
                  });

                  return; // Exit early since we handled the remove event
                }
              } else if ("modify" in event.type) {
                const modifyType = event.type.modify; // This is WatchEventKindModify
                if (event.paths.length === 0) {
                  return;
                } else {
                  const modifiedPath = event.paths[0];
                  if (
                    modifiedPath.endsWith(
                      `${appConfig.labelledJsonStartsWithString}.json`
                    )
                  ) {
                    if (imports.includes(modifiedPath)) {
                      updateTaskQueue(modifiedPath, "enqueued");
                    }
                  }
                }
              } else if (selectedData) {
                updateTaskQueue(selectedData, "enqueued");
              }
            }
          },
          { recursive: true }
        );
      } catch (error) {
        addError(`Error initializing file watchers: ${error}`, true);
      }
    };

    initializeWatchers();

    return () => {
      if (unwatchFn !== null) {
        unwatchFn();
        addInfo("File watcher cleaned up", true);
      }
    };
  }, [dataDirectory, appConfig]);

  const handleImport = async (forLabelling: boolean, path: string) => {
    if (forLabelling) {
      handleAddData(path);
    } else {
      try {
        const dir = await open({
          multiple: false,
          directory: true,
        });
        if (dir) {
          setProcessing(true);
          const success = await runNoChew(dir, path);

          if (success) {
            addSuccess("Data exported successfully", true);
          } else {
            addError("Error exporting data", true);
          }
        }
      } catch (error) {
        addError("Error exporting data", true);
      } finally {
        setProcessing(false);
      }
    }
  };

  const moveToArchiveFolder = async (path: string) => {
    if (!isValidState(dataDirectory)) return;

    const archiveFolder = appConfig.archiveFolderName || "archived";

    const movedToArchived = await moveFolderToArchived(
      path,
      dataDirectory,
      archiveFolder
    );

    if (movedToArchived.status === "error") {
      addError(movedToArchived.data, true);
      return;
    }
    await remove(path, { recursive: true });
    setImports(imports.filter((imported) => imported !== path));
    addSuccess(`Data moved to ${movedToArchived.data}`, true);
  };

  const exportData = async (dataPath: string) => {
    if (!appConfig) return;

    const location = await open({
      multiple: false,
      directory: true,
    });

    if (!location) {
      addError("No location selected", true);
      return;
    }

    try {
      setProcessing(true);
      const dataExported = await handleExportData(
        location,
        dataPath,
        appConfig
      );

      if (dataExported.success) {
        addSuccess(dataExported.message, true);
        updateTaskQueue(dataPath, "completed");
      } else {
        addError(dataExported.message, true);
        updateTaskQueue(dataPath, "errored");
      }
    } catch (error) {
      addError(`Error exporting data: ${error}`, true);
      updateTaskQueue(dataPath, "errored");
    } finally {
      setProcessing(false);
    }
  };

  async function maybeProcessNextTask(): Promise<void> {
    // Access the current enqueued tasks (assuming taskQueue is the latest value)
    if (taskQueue.enqueued.length === 0) {
      setProcessing(false);
      return;
    }

    // Remove the first task from the queue
    const nextTask = taskQueue.enqueued[0];
    // Update the taskQueue state by removing the first task.
    setTaskQueue((prevQueue) => ({
      ...prevQueue,
      enqueued: prevQueue.enqueued.slice(1),
    }));

    setProcessing(true);
    if (!isValidState(appConfig)) return;

    try {
      const status = await processTaskPipeline(nextTask, appConfig);
      updateTaskQueue(nextTask, status);
    } catch (error) {
      setProcessing(false);
      updateTaskQueue(nextTask, "errored");
    }
  }
  // Helper function that ensures the given task is only in the specified state.
  const updateTaskQueue = (
    task: string,
    newState: "enqueued" | "completed" | "waiting" | "errored" | "processing"
  ) => {
    setTaskQueue((prevQueue) => {
      // Remove the task from all arrays.
      const enqueued = prevQueue.enqueued.filter((t) => t !== task);
      const completed = prevQueue.completed.filter((t) => t !== task);
      const waiting = prevQueue.waiting.filter((t) => t !== task);
      const errored = prevQueue.errored.filter((t) => t !== task);

      // Add the task to the target array.
      if (newState === "enqueued") {
        setProcessing(true);
        return { enqueued: [...enqueued, task], completed, waiting, errored };
      } else if (newState === "processing") {
        setProcessing(true);
        return { enqueued: [...enqueued, task], completed, waiting, errored };
      } else if (newState === "completed") {
        setProcessing(false);
        return { enqueued, completed: [...completed, task], waiting, errored };
      } else if (newState === "waiting") {
        setProcessing(false);
        return { enqueued, completed, waiting: [...waiting, task], errored };
      } else {
        setProcessing(false);
        return { enqueued, completed, waiting, errored: [...errored, task] };
      }
    });
  };

  const redoLabels = async (path: string) => {
    setProcessing(true);
    const chunksFolderName = appConfig.chunksDirectoryName || "chunks";
    const verifiedFileName =
      appConfig.verifiedJsonStartsWithString || "verified";
    const labelledContent =
      appConfig.labelledJsonStartsWithString || "labelled";
    const mergedFileName = appConfig.mergedCsvFileName || "merged";

    console.log(
      "PATH, CHUNKS, VERIFIED",
      path,
      chunksFolderName,
      verifiedFileName
    );

    try {
      const labelledFile = await join(path, `${labelledContent}.json`);
      const labelledFileExists = await exists(labelledFile);

      if (!labelledFileExists) {
        addError("No labelled data found", true);
        return;
      }

      const labelledData = await readTextFile(labelledFile);
      const parsedData = JSON.parse(labelledData);

      if (Array.isArray(parsedData)) {
        const markers: Marker[] = parsedData.filter(
          (data): data is Marker =>
            typeof data === "object" &&
            "id" in data &&
            "frame" in data &&
            "timestamp" in data &&
            "mouth" in data &&
            "action" in data &&
            typeof data.id === "number" &&
            typeof data.frame === "number" &&
            typeof data.timestamp === "number" &&
            typeof data.mouth === "string" &&
            typeof data.action === "string"
        );

        const statusObject = { status: "incomplete" };
        await remove(labelledFile);

        const file = await create(labelledFile);

        await file.write(
          new TextEncoder().encode(JSON.stringify([statusObject, ...markers]))
        );
        await file.close();
      }

      const mergedCsv = await join(path, `${mergedFileName}.csv`);
      const mergedCsvExists = await exists(mergedCsv);

      if (mergedCsvExists) {
        await remove(mergedCsv);
      }

      const chunksFolder = await join(path, chunksFolderName);
      const chunksFolderExists = await exists(chunksFolder);

      if (chunksFolderExists) {
        await remove(chunksFolder, { recursive: true });
      }

      const verifiedFile = await join(path, `${verifiedFileName}.json`);
      const verifiedFileExists = await exists(verifiedFile);

      if (verifiedFileExists) {
        await remove(verifiedFile);
      }
    } catch (error) {
      addError("Error redoing labels", true);
    } finally {
      updateTaskQueue(path, "enqueued");
      setProcessing(false);
    }
  };

  const deleteData = async (path: string) => {
    try {
      setProcessing(true);
      await remove(path, {
        recursive: true,
      });
      setImports(imports.filter((imported) => imported !== path));
      addSuccess("Data deleted successfully", true);
    } catch (error) {
      addError("Error deleting data", true);
    } finally {
      setSelectedArchivedData(null);
      setSelectedData(null);
      setProcessing(false);
    }
  };

  return (
    <ChewingDataContext.Provider
      value={{
        fileSystemUpdate,
        handleImport,
        imports,
        exportData,
        selectedData,
        setSelectedData,
        taskQueue,
        refreshData,
        processing,
        redoLabels,
        moveToArchiveFolder,
        archived,
        selectedArchivedData,
        setSelectedArchivedData,
        deleteData,
      }}
    >
      <div>{children}</div>
    </ChewingDataContext.Provider>
  );
};

/**
 * @description Hook to use the ChewingData context
 * @returns {ChewingDataContextType}
 */
export const useChewingDataContext = (): ChewingDataContextType => {
  const context = useContext(ChewingDataContext);
  if (!context) {
    throw new Error(
      "useChewingDataContext must be used within a ChewingDataContextProvider"
    );
  }
  return context;
};
