import ImportedData from "./ImportedData";
import { Button } from "./ui/button";
import { useChewingDataContext } from "../context/ChewingDataContextProvider";
import { LoaderCircleIcon } from "lucide-react";

const ExportSelectedData = () => {
  const { selectedData, exportData, processing, moveToArchiveFolder } = useChewingDataContext();

  if (!selectedData) {
    return <div>No data selected</div>;
  }
  return (
    <div className="flex flex-col items-center">
      {processing && (
        <div className="text-lg font-bold text-center">
          Processing...
          <LoaderCircleIcon size={32} className="animate-spin" />
        </div>
      )}

      {!processing && (
        <div className="flex flex-row gap-3 text-lg items-center">
          Export?
          <Button onClick={() => exportData(selectedData)}>Export</Button>
        </div>
      )}

      <div className="flex flex-row gap-3 text-lg items-center">
        Archive?
        <Button onClick={() => moveToArchiveFolder(selectedData)}>Archive</Button>
      </div>


      
      <ImportedData />
    </div>
  );
};

export default ExportSelectedData;
