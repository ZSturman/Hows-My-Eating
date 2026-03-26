import { useAppRecord } from "../context/AppRecordContext";
import { useSelectedDataRecord } from "../context/DataRecordContext";

const ImportedDataList = () => {
  const { state: appRecordState} = useAppRecord();
  const { dispatch } = useSelectedDataRecord();

  const handleSelect = (dir: DataRecord) => {
    dispatch({ type: "SET_SELECTED_DATA_RECORD", payload: dir });
  };

  const handleDelete = (dir: DataRecord) => {
    // Dispatch an action or call a function to delete the directory
    dispatch({ type: "DELETING_DATA_RECORD", payload: dir });
  };

  return (
    <div style={{ padding: "20px", maxWidth: "600px", margin: "auto" }}>
      {appRecordState.dataDirectories.map((dir) => (
        <div
          key={dir.id}
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "10px",
            border: "1px solid #ddd",
            borderRadius: "4px",
            marginBottom: "10px",
          }}
        >
          <div>
            <div>Directory: {dir.dataDirectory}</div>
            <div>Synced? : {dir.isDataSynced ? "Yes" : "No"}</div>
          </div>
          <div style={{ display: "flex", gap: "10px" }}>
            <button
              onClick={() => handleSelect(dir)}
              style={{
                padding: "5px 10px",
                border: "none",
                borderRadius: "4px",
                backgroundColor: "#4CAF50",
                color: "white",
                cursor: "pointer",
              }}
            >
              Select
            </button>
            <button
              onClick={() => handleDelete(dir)}
              style={{
                padding: "5px 10px",
                border: "none",
                borderRadius: "4px",
                backgroundColor: "#f44336",
                color: "white",
                cursor: "pointer",
              }}
            >
              Delete
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ImportedDataList;