import { useEffect, useState } from "react";
import { listen } from "@tauri-apps/api/event";
import { useChewingDataContext } from "../context/ChewingDataContextProvider";
import { useAppContext } from "../context/AppContext";
import { isValidState } from "../utilities/isValid";
import { open } from "@tauri-apps/plugin-dialog";
import { Button } from "./ui/button";
import { Loader2 } from "lucide-react";

const DefaultWelcomeScreen = () => {
  const { dataDirectory, appConfig } = useAppContext();
  const { handleImport, processing } = useChewingDataContext();

  const [importedData, setImportedData] = useState<string | null>(null);

  useEffect(() => {
    let unlistenFn: () => void;
    async function attachListener() {
      unlistenFn = await listen<{ paths: string[] }>(
        "tauri://drag-drop",
        (event) => {
          if (event.payload?.paths?.length > 0) {
            console.log("Imported data", event.payload.paths[0]);
            setImportedData(event.payload.paths[0]);
          }
        }
      );
    }

    // Only attach the listener if dataDirectory is ready
    if (isValidState(dataDirectory) && isValidState(appConfig)) {
      attachListener();
    }

    return () => {
      if (unlistenFn) {
        unlistenFn();
      }
    };
  }, [dataDirectory, appConfig]);

  useEffect(() => {
    if (!processing) {
      setImportedData(null);
    }
  }, [processing]);

  const importButtonClicked = async () => {
    const dir = await open({
      multiple: false,
      directory: true,
    });
    if (dir) {
      setImportedData(dir);
    }
  };

  return (
    <div className="w-full h-full bg-zinc-900 text-zinc-100 flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <h1 className="text-4xl">
          Welcome to 'How's Your Eating?' data labeller
        </h1>
        {!importedData && (
          <div className="flex flex-col w-full items-center justify-center gap-5 mt-10 max-w-[400px] text-center">
            <h2>Import Data</h2>

            <p className="text-lg">
              To get started, import the folder that contains your data. There
              should be a .mov file and a .json in there
            </p>
            <button
              className="bg-zinc-500 text-zinc-100 px-4 py-2 rounded-md"
              onClick={importButtonClicked}
            >
              Import Data
            </button>
          </div>
        )}

{importedData && processing && (
          <div className="flex flex-col items-center gap-4">
            <div className="border border-zinc-500 p-4 rounded-md relative">
              <Button
                onClick={() => setImportedData(null)}
                variant="destructive"
                className="absolute top-0 right-0 m-2"
              >
                Clear
              </Button>
              <p>
                Processing data... This may take a few minutes depending on the
                size of the data <Loader2 className="animate-spin" />
              </p>
            </div>

            <div className="flex flex-row gap-4 items-center">
              <Button
                className="bg-zinc-500 text-zinc-100 px-4 py-2 rounded-md"
                onClick={() => handleImport(true, importedData)}
              >
                Contains Chewing Data?
              </Button>

              <Button
                className="bg-zinc-500 text-zinc-100 px-4 py-2 rounded-md"
                onClick={() => handleImport(false, importedData)}
              >
                Contains Non- Chewing Data
              </Button>
            </div>
          </div>
        )}

        {importedData && !processing && (
          <div className="flex flex-col items-center gap-4">
            <div className="border border-zinc-500 p-4 rounded-md relative">
              <Button
                onClick={() => setImportedData(null)}
                variant="destructive"
                className="absolute top-0 right-0 m-2"
              >
                Clear
              </Button>
              <p>{importedData}</p>
            </div>

            <div className="flex flex-row gap-4 items-center">
              <Button
                className="bg-zinc-500 text-zinc-100 px-4 py-2 rounded-md"
                onClick={() => handleImport(true, importedData)}
              >
                Contains Chewing Data?
              </Button>

              <Button
                className="bg-zinc-500 text-zinc-100 px-4 py-2 rounded-md"
                onClick={() => handleImport(false, importedData)}
              >
                Contains Non- Chewing Data
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DefaultWelcomeScreen;
