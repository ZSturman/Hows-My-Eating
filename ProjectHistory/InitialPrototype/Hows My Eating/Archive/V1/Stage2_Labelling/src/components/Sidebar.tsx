import React, { useEffect, useState } from "react";
import { ScrollArea } from "../components/ui/scroll-area";
import { useChewingDataContext } from "../context/ChewingDataContextProvider";
import { isValidState } from "../utilities/isValid";
import { Button } from "./ui/button";
import { Clock, ListCheck, ListMinus, ListX } from "lucide-react";

const Sidebar = () => {
  const { setSelectedData, imports, taskQueue, refreshData, archived, setSelectedArchivedData } =
    useChewingDataContext();
  const [importedFolders, setImportedFolders] = useState<
    {
      fullPath: string;
      folderName: string;
      statusIcon: React.ReactNode;
    }[]
  >([]);

  useEffect(() => {
    if (imports.length === 0) {
      return;
    }

    const folders = imports.map((data) => {
      const folderName = data.split("/").pop() || "";

      const isEqnqueued = taskQueue.enqueued.includes(data);
      const isCompleted = taskQueue.completed.includes(data);
      const isErrored = taskQueue.errored.includes(data);
      const isWaiting = taskQueue.waiting.includes(data);

      let statusIcon = <Clock size={24} />;
      if (isEqnqueued) {
        statusIcon = <ListMinus size={24} />;
      } else if (isCompleted) {
        statusIcon = <ListCheck size={24} />;
      } else if (isErrored) {
        statusIcon = <ListX size={24} />;
      } else if (isWaiting) {
        statusIcon = <Clock size={24} />;
      }

      return { fullPath: data, folderName, statusIcon };
    });

    setImportedFolders(folders);
  }, [imports, taskQueue]);

  const handleClick = (data: string, archived?: boolean) => {
    if (archived) {
      setSelectedData(null);
     setSelectedArchivedData(data);
      return;
    }
    setSelectedArchivedData(null)
    setSelectedData(data);
  };

  if (!isValidState(imports)) {
    return null;
  }

  if (imports.length === 0) {
    return null;
  }

  return (
    <ScrollArea className="h-screen rounded-md border p-4">
      <Button onClick={refreshData} variant={"outline"} className="mb-2 ">
        Refresh
      </Button>
      {importedFolders.length > 0 && (
        <div className="text-lg font-bold">Imported</div>
      )}
      {importedFolders.map((data, index) => (
        <Button
          key={index}
          onClick={() => handleClick(data.fullPath)}
          className="mb-2 w-full flex flex-row justify-start items-center"
        >
          <div></div>
          <div>{data.statusIcon}</div>
          <div>{data.folderName}</div>
        </Button>
      ))}

      {archived.length > 0 && (
        <div>
          <div className="text-lg font-bold mt-4">Archived</div>

          {archived.map((data, index) => (
            <Button
              key={index}
              onClick={() => handleClick(data, true)}
              className="mb-2 w-full flex flex-row justify-start items-center"
            >
              <div>{data}</div>
            </Button>
          ))}
        </div>
      )}
    </ScrollArea>
  );
};

export default Sidebar;
