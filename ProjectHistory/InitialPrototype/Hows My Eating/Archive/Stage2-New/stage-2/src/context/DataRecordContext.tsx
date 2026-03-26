import React, {
  createContext,
  useReducer,
  useContext,
  ReactNode,
  Dispatch,
  useEffect,
} from "react";
import { deleteDataFromAppData } from "../utils/deleteDataRecords";

// Data Record Actions
const SET_SELECTED_DATA_RECORD = "SET_SELECTED_DATA_RECORD";
const SET_CHECKING_DATA_RECORD = "SET_CHECKING_DATA_RECORD";
const GETTING_SELECTED_DATA_FRAMES = "GETTING_SELECTED_DATA_FRAMES";
const SET_SELECTED_DATA_RECORD_FRAMES = "SET_SELECTED_DATA_RECORD_FRAMES";
const DATA_RECORD_DELETED = "DATA_RECORD_DELETED";
const DELETING_DATA_RECORD = "DELETING_DATA_RECORD";
// Data Sync Actions
const SET_SYNCING = "SET_SYNCING";
const SET_SELECTED_DATA_IS_SYNCED = "SET_SELECTED_DATA_IS_SYNCED";
const SET_SELECTED_DATA_IS_NOT_SYNCED = "SET_SELECTED_DATA_IS_NOT_SYNCED";
// Labelling Actions
const SET_SELECTED_FRAME = "SET_SELECTED_FRAME";
const SET_PLAYING = "SET_PLAYING";

// Define actions for reducer
type DataRecordActions =
  | {
      type: typeof SET_SELECTED_DATA_RECORD;
      payload: DataRecord;
    }
  | { type: typeof GETTING_SELECTED_DATA_FRAMES; payload: DataRecord }
  | { type: typeof DELETING_DATA_RECORD; payload: DataRecord }
  | { type: typeof DATA_RECORD_DELETED; payload: DataRecord }
  | { type: typeof SET_CHECKING_DATA_RECORD; payload: boolean }
  | { type: typeof SET_SYNCING; payload: boolean }
  | { type: typeof SET_SELECTED_DATA_IS_SYNCED }
  | { type: typeof SET_SELECTED_DATA_IS_NOT_SYNCED }
  | {
      type: typeof SET_SELECTED_DATA_RECORD_FRAMES;
      payload: Frame[];
    }
  | { type: typeof SET_SELECTED_FRAME; payload: Frame | null }
  | { type: typeof SET_PLAYING; payload: boolean };

type SelectedDataRecordState = {
  selectedDataRecord: DataRecord | null;
  selectedDataRecordFrames: Frame[] | null;
  currentFrame: Frame | null;
  isPlaying: boolean;
  isDeleting: boolean;
  isSyncing: boolean;
  isLoading: boolean;
};

const initialSelectedDataRecordState: SelectedDataRecordState = {
  selectedDataRecord: null,
  selectedDataRecordFrames: null,
  currentFrame: null,
  isPlaying: false,
  isDeleting: false,
  isSyncing: false,
  isLoading: false,
};

// Context for App Records and Session State
const DataRecordContext = createContext<{
  state: SelectedDataRecordState;
  dispatch: Dispatch<DataRecordActions>;
}>({
  state: initialSelectedDataRecordState,
  dispatch: () => undefined,
});

const selectedDataRecordReducer = (
  state: SelectedDataRecordState,
  action: DataRecordActions
): SelectedDataRecordState => {
  switch (action.type) {
    case SET_SELECTED_DATA_RECORD:
      return {
        ...state,
        selectedDataRecord: action.payload,
      };
    case GETTING_SELECTED_DATA_FRAMES:
      return {
        ...state,
        isLoading: true,
      };
    case SET_SELECTED_DATA_RECORD_FRAMES:
      return {
        ...state,
        selectedDataRecordFrames: action.payload,
        isLoading: false,
      };
    case SET_SELECTED_FRAME:
      return {
        ...state,
        currentFrame: action.payload,
      };
    case SET_PLAYING:
      return {
        ...state,
        isPlaying: action.payload,
      };
    case SET_CHECKING_DATA_RECORD:
      return {
        ...state,
        isLoading: true,
      };
    case SET_SYNCING:
      return {
        ...state,
        isSyncing: action.payload,
      };
    case SET_SELECTED_DATA_IS_SYNCED:
      return {
        ...state,
        selectedDataRecord: {
          ...state.selectedDataRecord!,
          isDataSynced: true,
        },
      };
    case SET_SELECTED_DATA_IS_NOT_SYNCED:
      return {
        ...state,
        selectedDataRecord: {
          ...state.selectedDataRecord!,
          isDataSynced: false,
        },
      };
    case DELETING_DATA_RECORD:
      return {
        ...state,
        isDeleting: true,
      };
    case DATA_RECORD_DELETED:
      return {
        ...state,
        isDeleting: false,
      };
    default:
      return state;
  }
};

// Provider Component
export const DataRecordProvider: React.FC<{
  children: ReactNode;
  currentState?: SelectedDataRecordState;
}> = ({ children, currentState }) => {
  const [state, dispatch] = useReducer(
    selectedDataRecordReducer,
    currentState ? currentState : initialSelectedDataRecordState
  );

  useEffect(() => {
    const deleteDataRecord = async () => {
      if (state.isDeleting) {
        if (state.selectedDataRecord) {
          console.log("Deleting data record:", state.selectedDataRecord);
          const deletedDirectory = deleteDataFromAppData(
            state.selectedDataRecord
          );
          console.log("Deleted Directory: ", deletedDirectory);
          dispatch({
            type: DATA_RECORD_DELETED,
            payload: state.selectedDataRecord,
          });
        }
      }
    };

    deleteDataRecord();
  }, [state.isDeleting]);

  return (
    <DataRecordContext.Provider value={{ state, dispatch }}>
      {children}
    </DataRecordContext.Provider>
  );
};

export const useSelectedDataRecord = () =>
  useContext(DataRecordContext);
