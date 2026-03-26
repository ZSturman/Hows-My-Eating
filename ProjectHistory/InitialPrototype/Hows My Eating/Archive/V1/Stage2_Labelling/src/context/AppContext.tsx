import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import { exists, mkdir, create, readTextFile } from "@tauri-apps/plugin-fs";
import { join, appDataDir } from "@tauri-apps/api/path";
import { isValidState } from "../utilities/isValid";

const defaultAppConfig: AppConfig = {
  outputProcessedVideo: true,
  requireMainVideoThumbnail: true,
  requireScrubbingThumbnails: true,
  labelledJsonStartsWithString: "labelled",
  importedDataParentFolderName: "imported",
  mergedCsvFileName: "merged",
  chunksDirectoryName: "chunks",
  verifiedJsonStartsWithString: "verified",
  exportFolderName: "export",
  importFolderName: "imported",
  archiveFolderName: "archived",
  processVisualsCsvFileName: "process-visuals",
  movInfoFileName: "mov-info",
  compareVisualsCsvFileName: "compare-visuals",

};

type AppContextType = {
  dataDirectory: string | LoadingState;
  //trackedDataJsonDirectoryPath: string | LoadingState;
  appConfig: AppConfig;
};

// Default values for context
const defaultAppContext: AppContextType = {
  dataDirectory: null,
  //trackedDataJsonDirectoryPath: null,
  appConfig: defaultAppConfig,
};

// Create Context
const AppContext = createContext<AppContextType>(defaultAppContext);

// Provider Component
export const AppContextProvider = ({ children }: { children: ReactNode }) => {
  const [dataDirectory, setAppDataDir] = useState<string | LoadingState>(null);
  //const [trackedDataJsonDirectoryPath, setTrackedDataJsonDirectoryPath] =useState<string | LoadingState>(null);
  const [appConfig, setAppConfig] = useState<AppConfig>(defaultAppConfig);

  useEffect(() => {
    const initializeAppDirectory = async () => {
      setAppDataDir("loading");
      try {
        const appDataDirectoryPath = await setupAppDirectory();
        await setupAppConfig(appDataDirectoryPath);
      } catch {
        setAppDataDir("error");
      }
    };

    const initializeProvider = async () => {
      try {
        await initializeAppDirectory();
      } catch (e) {
        console.error("Error during initialization:", e);
      }
    };

    initializeProvider();
  }, []);

  useEffect(() => {
    if (!isValidState(dataDirectory)) {
      return;
    }

    //setUpTrackedDataJson();
  }, [dataDirectory]);

  const setupAppDirectory = async (): Promise<string> => {
    const appDataDirPath = await appDataDir();
    const appDataDirExists = await exists(appDataDirPath);

    if (!appDataDirExists) {
      await mkdir(appDataDirPath, { recursive: true });
      console.log("App data directory created");
    }
    setAppDataDir(appDataDirPath);
    return appDataDirPath;
  };

  const setupAppConfig = async (
    appDataDirectoryPath: string
  ): Promise<string> => {
    const appConfigPath = await join(appDataDirectoryPath, "app-config.json");
    const appConfigExists = await exists(appConfigPath);

    if (!appConfigExists) {
      const file = await create(appConfigPath);
      const data = new TextEncoder().encode(JSON.stringify(defaultAppConfig));
      await file.write(data);
      await file.close();
      setAppConfig(defaultAppConfig);
      return appConfigPath;
    }

    const configFileContents = await readTextFile(appConfigPath);

    let appConfigData: Partial<AppConfig> = {};

    try {
      appConfigData = JSON.parse(configFileContents) as Partial<AppConfig>;
    } catch (error) {
      console.error("Error parsing app config:", error);
      // If the file is corrupted, reset to default config
      const file = await create(appConfigPath);
      const data = new TextEncoder().encode(
        JSON.stringify(defaultAppConfig, null, 2)
      );
      await file.write(data);
      await file.close();
      setAppConfig(defaultAppConfig);
      return appConfigPath;
    }

    // Merge existing config with default config to fill in missing values
    const updatedConfig = { ...defaultAppConfig, ...appConfigData };

    // Check if there were missing values that got filled
    if (JSON.stringify(updatedConfig) !== JSON.stringify(appConfigData)) {
      // Write the updated config back to the file
      const file = await create(appConfigPath);
      const data = new TextEncoder().encode(
        JSON.stringify(updatedConfig, null, 2)
      );
      await file.write(data);
      await file.close();
    }

    setAppConfig(updatedConfig);
    return appConfigPath;
  };

  return (
    <AppContext.Provider
      value={{
        dataDirectory,
        //trackedDataJsonDirectoryPath,
        appConfig,
      }}
    >
      <div>{children}</div>
    </AppContext.Provider>
  );
};

export const useAppContext = () => {
  if (!AppContext) {
    throw new Error("useAppContext must be used within an AppContextProvider");
  }
  return useContext(AppContext);
};
