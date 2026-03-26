import { useEffect, useState } from "react";
import {
  create,
  DirEntry,
  exists,
  readDir,
  readTextFile,
  open,
  writeTextFile,
} from "@tauri-apps/plugin-fs";
import { join } from "@tauri-apps/api/path";
import { ScrollArea } from "../ui/scroll-area";
import { Button } from "../ui/button";
import VideoMarker from "../labelling/VideoMarker";
import { MovInfo } from "../../types/ChewingData.types";
import { Marker } from "../../types/Markers";
import { useAppContext } from "../../context/AppContext";
import { isValidState } from "../../utilities/isValid";
import { useChewingDataContext } from "../../context/ChewingDataContextProvider";

const findFilePath = async (
  directoryContents: DirEntry[],
  selectedData: string,
  fileNamePattern: string,
  fileExtension: string
) => {
  const file = directoryContents.find(
    (file) =>
      file.name?.startsWith(fileNamePattern) &&
      file.name?.endsWith(fileExtension)
  );
  return file ? await join(selectedData, file.name) : null;
};

const LabelDataContainer = () => {
  const { appConfig } = useAppContext();
  const { selectedData } = useChewingDataContext();
  const [movInfo, setMovInfo] = useState<MovInfo | null>(null);
  const [markers, setMarkers] = useState<Marker[] | null>(null);
  const [labelledDataStatus, setLabelledDataStatus] =
    useState<JsonStatusObject>({
      status: "incomplete",
    });

  useEffect(() => {
    if (!selectedData) return;

    const fetchMovData = async () => {
      try {
        const movInfoFileName = appConfig.movInfoFileName || "mov-info";
        const directoryContents = await readDir(selectedData);
        const movInfoFilePath = await findFilePath(
          directoryContents,
          selectedData,
          movInfoFileName,
          ".json"
        );

        if (movInfoFilePath) {
          const movInfoFile = await readTextFile(movInfoFilePath);
          const parsedData = JSON.parse(movInfoFile);
          const movInfoData: MovInfo = {
            videoPath: parsedData.video_path,
            duration: parsedData.duration,
            fps: parsedData.fps,
            totalFrames: parsedData.total_frames,
            width: parsedData.width,
            height: parsedData.height,
          };
          setMovInfo(movInfoData);
        }
      } catch (error) {
        console.error("Error fetching selected data:", error);
      }
    };

    const fetchLabelledData = async () => {
      try {
        if (!isValidState(appConfig)) return;

        const labelledDataJsonPath = await join(
          selectedData,
          `${appConfig.labelledJsonStartsWithString}.json`
        );
        const labelledDataJsonExists = await exists(labelledDataJsonPath);

        if (!labelledDataJsonExists) {
          const file = await create(labelledDataJsonPath);
          const statusObject = [{ status: labelledDataStatus }];
          await file.write(
            new TextEncoder().encode(JSON.stringify(statusObject))
          );
          await file.close();

          setMarkers([]);
          setLabelledDataStatus({
            status: "incomplete",
          });
        } else {
          const labelledData = await readTextFile(labelledDataJsonPath);
          const parsedData = JSON.parse(labelledData);

          if (Array.isArray(parsedData)) {
            // Find the object with the key "status" and use it's value for the labelledDataStatus
            const status = parsedData.find(
              (data) => typeof data === "object" && "status" in data
            );
            if (status) {
              setLabelledDataStatus(status.status);
            } else {
              const file = await open(labelledDataJsonPath, {
                append: true,
              });
              const statusObject = [{ status: labelledDataStatus }];
              await file.write(
                new TextEncoder().encode(JSON.stringify(statusObject))
              );
              await file.close();
            }
            const filteredData: Marker[] = parsedData.filter(
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
            setMarkers(filteredData);
          } else {
            console.error("Invalid labelled data format");
          }
        }
      } catch (error) {
        console.error("Error fetching selected data:", error);
      }
    };

    const fetchData = async () => {
      if (!movInfo) {
        await fetchMovData();
      }

      if (!markers) {
        await fetchLabelledData();
      }
    };

    fetchData();
  }, [selectedData, movInfo]);

  const updateMarkers = async (frame: number, newMarker: Marker) => {
    if (!markers) return;
    // Replace any existing marker at the same frame.
    setMarkers((prevMarkers) => {
      if (!prevMarkers) return [newMarker];
      const existingIndex = prevMarkers.findIndex((m) => m.frame === frame);
      if (existingIndex !== -1) {
        const updatedMarkers = [...prevMarkers];
        updatedMarkers[existingIndex] = newMarker;
        return updatedMarkers;
      }
      return [newMarker, ...prevMarkers];
    });
  };

  // New function to delete a marker by its id
  const deleteMarker = (markerId: number) => {
    setMarkers((prevMarkers) =>
      prevMarkers ? prevMarkers.filter((marker) => marker.id !== markerId) : []
    );
  };

  // New function to clear all markers
  const clearMarkers = () => {
    setMarkers([]);
  };

  const handleSaveAndContinueLater = async () => {
    try {
      if (!isValidState(selectedData)) return;
      if (!markers) return;

      const labelledDataJsonPath = await join(
        selectedData,
        `${appConfig.labelledJsonStartsWithString}.json`
      );

      console.log("Saving labelled data for later:", labelledDataJsonPath);
      const statusObject = { status: labelledDataStatus };

      const markersObject = markers.map((marker) => {
        return {
          id: marker.id,
          frame: marker.frame,
          timestamp: marker.timestamp,
          mouth: marker.mouth,
          action: marker.action,
        };
      });

      const contents = JSON.stringify([statusObject, ...markersObject]);
      await writeTextFile(labelledDataJsonPath, contents);
    } catch (error) {
      console.error("Error saving labelled data:", error);
    }
  };

  const handleFinished = async () => {
    if (!isValidState(selectedData)) return;
    if (!markers) return;

    try {
      setLabelledDataStatus({
        status: "complete",
      });

      const labelledDataJsonPath = await join(
        selectedData,
        `${appConfig.labelledJsonStartsWithString}.json`
      );

      const statusObject: JsonStatusObject = { status: "complete" };
      const markersObject = markers.map((marker) => {
        return {
          id: marker.id,
          frame: marker.frame,
          timestamp: marker.timestamp,
          mouth: marker.mouth,
          action: marker.action,
        };
      });
      const contents = JSON.stringify([statusObject, ...markersObject]);
      await writeTextFile(labelledDataJsonPath, contents);
    } catch (error) {
      console.error("Error saving labelled data:", error);
    }
  };

  if (!selectedData) return null;

  if (!movInfo) return null;

  if (!markers) return null;

  return (
    <div className="h-full overflow-auto">
      <div className="flex flex-row itemx-center gap-2">
        <Button onClick={handleSaveAndContinueLater}>
          Save and Continue Later
        </Button>

        <Button onClick={handleFinished}>Finished</Button>
      </div>

      <VideoMarker
        movInfo={movInfo}
        markers={markers}
        updateMarkers={updateMarkers}
        deleteMarker={deleteMarker}
        clearMarkers={clearMarkers}
      />
    </div>
  );
};

export default LabelDataContainer;
