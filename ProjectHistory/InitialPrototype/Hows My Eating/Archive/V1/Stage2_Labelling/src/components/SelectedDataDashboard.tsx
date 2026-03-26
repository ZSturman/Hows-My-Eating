import { useChewingDataContext } from "../context/ChewingDataContextProvider";
import { Button } from "./ui/button";
import LabelDatatContainer from "./labelling/LabelDatatContainer";
import { useEffect, useState } from "react";
import { isValidState } from "../utilities/isValid";
import { useAppContext } from "../context/AppContext";
import { join } from "@tauri-apps/api/path";
import { exists, readTextFile } from "@tauri-apps/plugin-fs";
import VerifyDataContainer from "./verify/VerifyDataContainer";
import { VideoChunkStatus } from "@/types/Markers";
import ExportSelectedData from "./ExportSelectedData";
import { ask } from "@tauri-apps/plugin-dialog";
import { ScrollArea } from "@radix-ui/react-scroll-area";
import ImportedData from "./ImportedData";


const SelectedDataDashboard = () => {
  const { appConfig } = useAppContext();
  const { fileSystemUpdate, redoLabels, selectedData, selectedArchivedData, deleteData } = useChewingDataContext();
  const [mergedData, setMergedData] = useState<string | null>(null);
  const [verifiedData, setVerifiedData] = useState<string | null>(null);
  const [verifiedDataStatus, setVerifiedDataStatus] =
    useState<JsonStatusObject>({
      status: "incomplete",
    });
  const [selectedDataName, setSelectedDataName] = useState<string | null>(null);

  const [updteLabels, setUpdateLabels] = useState<boolean>(false);
  const [isArchived, setIsArchived] = useState<boolean>(false);

  useEffect(() => {
    const fetchSelectedDataName = async () => {
      if (!selectedData && !selectedArchivedData) return;
      if (selectedData) {

        const selectedDataName = selectedData.split("/").pop() || "";
        setSelectedDataName(selectedDataName);
      }if (selectedArchivedData){
        const selectedDataName = selectedArchivedData.split("/").pop() || "";
        setSelectedDataName(selectedDataName);
        setIsArchived(true);
      }
    };

    setIsArchived(false);
    fetchSelectedDataName();
    setMergedData(null);
    setVerifiedData(null);
  }, [selectedData]);

  useEffect(() => {
    const fetchMergedData = async () => {
      try {
        if (!isValidState(appConfig) || !isValidState(selectedData)) return;

        const mergedCsvFilePath = await join(
          selectedData,
          `${appConfig.mergedCsvFileName}.csv`
        );
        const mergedCsvExists = await exists(mergedCsvFilePath);

        if (mergedCsvExists) {
          setMergedData(mergedCsvFilePath);
        }
      } catch (error) {
        console.error("Error fetching selected data:", error);
      }
    };

    const fetchVerifiedData = async () => {
      try {
        if (!isValidState(appConfig) || !isValidState(selectedData)) return;

        const verifiedFilePath = await join(
          selectedData,
          `${appConfig.verifiedJsonStartsWithString || "verified"}.json`
        );
        const verifiedFileExists = await exists(verifiedFilePath);

        if (verifiedFileExists) {
          setVerifiedData(verifiedFilePath);

          const fetchedVerifiedData = await readTextFile(verifiedFilePath);
          const parsedData = JSON.parse(fetchedVerifiedData);

          if (Array.isArray(parsedData)) {
            // Find the object with the key "status" and use it's value for the labelledDataStatus
            const status = parsedData.find(
              (data) => typeof data === "object" && "status" in data
            );
            if (status) {
              setVerifiedDataStatus(status);

              if (status.status === "complete") {
                // Check all the other objects in the array and see if any of them have "verified" == false
                const verifiedData = parsedData.filter(
                  (data): data is VideoChunkStatus => "verified" in data
                );

                if (verifiedData.some((data) => !data.verified)) {
                  setUpdateLabels(true);
                }
              }
            }
          }
        }
      } catch (error) {
        console.error("Error fetching selected data:", error);
      }
    };

    const fetchData = async () => {
      if (!mergedData) {
        await fetchMergedData();
      }

      if (!verifiedData) {
        await fetchVerifiedData();
      }
    };

    fetchData();
  }, [fileSystemUpdate, selectedData]);

  const handleRedoLabels = async () => {
    if (!selectedData) return
    const answer = await ask(
      "Previously labelled content will still be saved.",
      {
        title:
          "This action will remove all verified data and return you to the Labelling step. Are you sure you want to continue?",
        kind: "warning",
      }
    );

    if (answer === null) {
      return;
    }

    if (answer) {
      redoLabels(selectedData);
    }
  };

  const handleDeleteData = async () => {
    if (!selectedData) return;
    const answer = await ask(
      "This action cannot be undone.",
      {
        title: "Are you sure you want to delete this data?",
        kind: "warning",
      }
    );

    if (answer === null) {
      return;
    }

    if (answer) {
      deleteData(selectedData);
    }
  }

  if (!selectedData && !selectedArchivedData) return;

  if (isArchived) {
    return (
      <div>
        <div>
          <div className="w-full text-center font-bold text-3xl mt-4 mb-6">
            {selectedDataName}
          </div>
        </div>
        <div className="text-center text-lg">
          This data is archived and cannot be modified.
        </div>

        <div>
          <ImportedData />
        </div>
      </div>
    );
  }

  return (
    <ScrollArea className="h-[90vh] p-4">

      <div className="flex justify-between items-center w-full p-2">
        {verifiedData && (
          <Button onClick={handleRedoLabels}>Redo Labels</Button>
        )}

        <Button onClick={handleDeleteData} variant={"outline"}>
          Delete
        </Button>
      <div className="w-full text-center font-bold text-3xl mt-4 mb-6">
        {selectedDataName}
      </div>
      </div>

      {!mergedData && <LabelDatatContainer key={selectedData || selectedArchivedData} />}

      {mergedData && !verifiedData && (
        <div
          role="status"
          className="flex flex-col items-center justify-center h-96 bg-zinc-800"
        >
          <div>
            <p className="text-lg font-semibold text-gray-200 dark:text-gray-600 my-10">
              Processing Data...
            </p>
          </div>
          <svg
            aria-hidden="true"
            className="w-8 h-8 text-gray-200 animate-spin dark:text-gray-600 fill-blue-600"
            viewBox="0 0 100 101"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z"
              fill="currentColor"
            />
            <path
              d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z"
              fill="currentFill"
            />
          </svg>
          <span className="sr-only">Loading...</span>
        </div>
      )}

      {verifiedData && verifiedDataStatus.status === "incomplete" && (
        <VerifyDataContainer key={selectedData || selectedArchivedData} />
      )}

      {updteLabels &&
        verifiedData &&
        verifiedDataStatus.status === "complete" && <LabelDatatContainer key={selectedData || selectedArchivedData}  />}

      {verifiedDataStatus.status === "complete" && (
        <div>
          <ExportSelectedData key={selectedData || selectedArchivedData} />
        </div>
      )}
    </ScrollArea>
  );
};

export default SelectedDataDashboard;
