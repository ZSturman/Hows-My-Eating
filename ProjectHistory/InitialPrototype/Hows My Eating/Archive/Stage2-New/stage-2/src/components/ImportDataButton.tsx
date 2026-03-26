// src/components/ImportData.tsx

import { useEffect } from "react";
import { useImportContext } from "../context/ImportContext";
import { useAppRecord } from "../context/AppRecordContext";



export const ImportDataButton: React.FC = () => {
  const { state, dispatch, successPayload } = useImportContext();
  const {  dispatch: appRecordDispatch } = useAppRecord();

  useEffect(() => {

    if (state === "IMPORT_COMPLETE") {
      appRecordDispatch({ type: "ADD_DATA_RECORD", payload: successPayload})
    }

  }, [state]);

  const handleImport = async () => {
    dispatch("IMPORTING" );

  };

  return (
    <div>
      <h2>Import Data</h2>
      <button
        onClick={handleImport}
        disabled={state === "IMPORTING" || state === "IMPORTING_CANCELLED"}
      >
        {state === "IMPORTING"
          ? "Importing..."
          : "Select Data To Import"}
      </button>
    </div>
  );
};
