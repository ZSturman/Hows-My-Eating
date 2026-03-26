import { useEffect, useState } from "react";
import {
  create,
  exists,
  readTextFile,
  open,
  writeTextFile,
} from "@tauri-apps/plugin-fs";
import { join } from "@tauri-apps/api/path";
import { useChewingDataContext } from "../../context/ChewingDataContextProvider";
import { ScrollArea } from "../ui/scroll-area";
import { Button } from "../ui/button";
import { VideoChunkStatus } from "../../types/Markers";
import { useAppContext } from "../../context/AppContext";
import { isValidState } from "../../utilities/isValid";
import { VideoCarousel } from "./VideoCarousel";

const VerifyDataContainer = () => {
  const { appConfig } = useAppContext();
  const { selectedData } = useChewingDataContext();
  const [verifiedDataStatus, setVerifiedDataStatus] =
    useState<JsonStatusObject>({
      status: "incomplete",
    });
  const [verifiedData, setVerifiedData] = useState<VideoChunkStatus[] | null>(
    null
  );

  useEffect(() => {
    if (!selectedData) return;

    const fetchVerifiedData = async () => {
      try {
        if (!isValidState(appConfig)) return;

        const verifiedDataJsonPath = await join(
          selectedData,
          `${appConfig.verifiedJsonStartsWithString}.json`
        );
        const verifiedDataJsonExists = await exists(verifiedDataJsonPath);

        if (!verifiedDataJsonExists) {
          const file = await create(verifiedDataJsonPath);
          const statusObject = [{ status: verifiedDataStatus }];
          await file.write(
            new TextEncoder().encode(JSON.stringify(statusObject))
          );
          await file.close();

          setVerifiedData([]);
          setVerifiedDataStatus({
            status: "incomplete",
          });
        } else {
          const verifiedData = await readTextFile(verifiedDataJsonPath);
          const parsedData = JSON.parse(verifiedData);

          if (Array.isArray(parsedData)) {
            // Find the object with the key "status" and use it's value for the verifiedDataStatus
            const status = parsedData.find(
              (data) => typeof data === "object" && "status" in data
            );
            if (status) {
              setVerifiedDataStatus(status.status);
            } else {
              const file = await open(verifiedDataJsonPath, {
                append: true,
              });
              const statusObject = [{ status: verifiedDataStatus }];
              await file.write(
                new TextEncoder().encode(JSON.stringify(statusObject))
              );
              await file.close();
            }
            const filteredData: VideoChunkStatus[] = parsedData.filter(
              (data): data is VideoChunkStatus =>
                typeof data === "object" &&
                "fileName" in data &&
                "filePath" in data &&
                "originalValue" in data &&
                "frameStart" in data &&
                "frameEnd" in data &&
                "verified" in data &&
                typeof data.fileName === "string" &&
                typeof data.filePath === "string" &&
                typeof data.frameStart === "number" &&
                typeof data.frameEnd === "number" &&
                typeof data.verified === "boolean"
            );
            setVerifiedData(filteredData);
          } else {
            console.error("Invalid verified data format");
          }
        }
      } catch (error) {
        console.error("Error fetching selected data:", error);
      }
    };

    const fetchData = async () => {
      if (!verifiedData) {
        await fetchVerifiedData();
      }
    };

    fetchData();
  }, [selectedData, verifiedData]);

  const handleSaveAndContinueLater = async () => {
    try {
      if (!isValidState(selectedData)) return;
      if (!verifiedData) return;

      const verifiedJsonFilePath = await join(
        selectedData,
        `${appConfig.verifiedJsonStartsWithString || "verified"}.json`
      );

      console.log("Saving verified data for later:", verifiedJsonFilePath);
      const statusObject = { status: verifiedDataStatus };

      const contents = JSON.stringify([statusObject, ...verifiedData]);

      await writeTextFile(verifiedJsonFilePath, contents);
    } catch (error) {
      console.error("Error saving verified data:", error);
    }
  };

  const handleFinished = async () => {
    if (!isValidState(selectedData)) return;
    if (!verifiedData) return;

    if (
      verifiedData.filter((data) => data.verified).length !==
      verifiedData.length
    ) {
      alert("Please verify all data before finishing");
      return;
    }

    try {
      setVerifiedDataStatus({
        status: "complete",
      });

      const verifiedJsonFilePath = await join(
        selectedData,
        `${appConfig.verifiedJsonStartsWithString || "verified"}.json`
      );

      const statusObject: JsonStatusObject = { status: "complete" };

      const contents = JSON.stringify([statusObject, ...verifiedData]);
      await writeTextFile(verifiedJsonFilePath, contents);
    } catch (error) {
      console.error("Error saving verified data:", error);
    }
  };

  const handleVerify = (index: number, correct: boolean) => {
    setVerifiedData((prev) => {
      if (!prev) return null;
      const newVerifiedData = [...prev];
      newVerifiedData[index] = {
        ...newVerifiedData[index],
        correct,
        verified: true,
      };
      return newVerifiedData;
    });
  };

  const handleUndo = (index: number) => {
    setVerifiedData((prev) => {
      if (!prev) return null;
      const newVerifiedData = [...prev];
      newVerifiedData[index] = { ...newVerifiedData[index], verified: false };
      return newVerifiedData;
    });
  };

  if (!selectedData) return null;

  if (!verifiedData) return null;

  return (
    <ScrollArea className="h-[72]">
    <div className="p-4 h-full">
      <div className="flex flex-row itemx-center gap-2">
        <Button onClick={handleSaveAndContinueLater}>
          Save and Continue Later
        </Button>

        <Button
          onClick={handleFinished}
          disabled={
            verifiedData.filter((data) => data.verified).length !==
            verifiedData.length
          }
        >
          Finished
        </Button>
      </div>

      <div>
        {verifiedData.filter((data) => data.verified).length} /{" "}
        {verifiedData.length} verified
      </div>


      <VideoCarousel
        videos={verifiedData}
        handleVerify={handleVerify}
        handleUndo={handleUndo}
        />
    </div>
        </ScrollArea>
  );
};

export default VerifyDataContainer;
