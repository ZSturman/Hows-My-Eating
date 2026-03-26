import { useEffect, useState } from "react";
import { useSelectedDataRecord } from "../context/DataRecordContext";
import LabellingAndPlayback from "./LabellingAndPlayback";
import { LabelProvider } from "../context/LabellingContext";



const SelectedDataRecord = () => {
  const { state } = useSelectedDataRecord();

  const [screenHeight, setScreenHeight] = useState<number>(window.innerHeight);
  const [screenWidth, setScreenWidth] = useState<number>(window.innerWidth);

  useEffect(() => {
    const handleResize = () => {
      setScreenHeight(window.innerHeight);
      setScreenWidth(window.innerWidth);
    };

    // Set initial dimensions
    handleResize();

    // Add event listener to update dimensions on resize
    window.addEventListener("resize", handleResize);

    // Cleanup event listener on component unmount
    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  const videoContainerHeight = state.selectedDataRecord
    ? state.selectedDataRecord.movData.height > screenHeight
      ? `${screenHeight}px`
      : `${state.selectedDataRecord.movData.height}px`
    : "auto";

  return (
    <div className="mt-8 w-full">
    

      {state.selectedDataRecord ? (
        <LabelProvider selectedData={state.selectedDataRecord}>
        <div
          className={`overflow-hidden items-center justify-center w-full`}
          style={{ maxHeight: videoContainerHeight }}
        >
          <LabellingAndPlayback />
        </div>
        </LabelProvider>
      ) : (
        <div>
          <h2 className="text-lg text-gray-600">No Data Record Selected</h2>
        </div>
      )}
    </div>
  );
};


export default SelectedDataRecord;