import { createContext, useReducer, useContext, useEffect } from "react";

type OnboardingStatus = "NOT_STARTED" | "IN_PROGRESS" | "COMPLETED";

type OnBoardingStage =
  | "WELCOME"
  | "IMPORT_DATA"
  | "SYNC_DATA"
  | "LABEL_DATA"
  | "EXPORT_DATA"
  | "FINISHED";

type PlaybackStatus =
  | false // Playback is not running
  | "PLAYING" // Playback is running
  | "PAUSED" // Playback is paused
  | "PLAYBACK_ERROR"; // An error occurred during playback

type DeleteStatus =
  | false // No delete process is currently running
  | "CONFIRMING" // Confirming the deletion of the selected data record
  | "DELETING" // Deleting the selected data record
  | "DELETE_COMPLETE" // Delete process is complete
  | "DELETE_ERROR"; // An error occurred during the delete process

type SyncStatus =
  | false // No sync process is currently running
  | "SYNCING" // Sync process is running
  | "SYNC_COMPLETE" // Sync process is complete
  | "SYNC_ERROR"; // An error occurred during the sync process

type SavingStatus =
  | false // No save process is currently running
  | "SAVING" // Save process is running
  | "SAVE_COMPLETE" // Save process is complete
  | "SAVE_ERROR"; // An error occurred during the save process

type ExportStatus =
  | false
  | "EXPORTING" // Export process is running
  | "EXPORT_COMPLETE" // Export process is complete
  | "EXPORT_ERROR"; // An error occurred during the export process

type SessionState = {
  dirty: {
    status: boolean;
    dataRecord?: string; // id of the data record
    appRecord?: boolean; // the app record file
  };
  user: {
    firstTimeHere: boolean;
    onboardingStatus: OnboardingStatus;
    stage: OnBoardingStage;
  };
  dataRecordSelection: {
    record: DataRecord;
    frames: Frame[];
  } | null;
  playback: {
    status: PlaybackStatus;
    currentFrame: Frame | null;
  };
  deleting: {
    status: DeleteStatus;
    dataRecord?: DataRecord;
  };
  syncing: {
    status: SyncStatus;
    dataRecord?: DataRecord;
  };
  isLoading: boolean;
  saving: {
    status: SavingStatus;
  };
  exporting: {
    status: ExportStatus;
    dataRecords: DataRecord[];
  };
};

type SessionAction =
  | {
      type: "SET_DIRTY";
      status: boolean;
      dataRecord?: string;
      appRecord?: boolean;
    }
  | {
      type: "SET_USER";
      firstTimeHere: boolean;
      onboardingStatus: OnboardingStatus;
      stage: OnBoardingStage;
    }
  | { type: "SET_DATA_RECORD_SELECTION"; record: DataRecord; frames: Frame[] }
  | { type: "CLEAR_DATA_RECORD_SELECTION" }
  | { type: "SET_PLAYBACK"; status: PlaybackStatus; currentFrame: Frame | null }
  | { type: "SET_DELETING"; status: DeleteStatus; dataRecord?: DataRecord }
  | { type: "SET_SYNCING"; status: SyncStatus; dataRecord?: DataRecord }
  | { type: "SET_LOADING"; status: boolean }
  | { type: "SET_SAVING"; status: SavingStatus }
  | { type: "SET_EXPORTING"; status: ExportStatus; dataRecords: DataRecord[] };

const initialSessionState: SessionState = {
  dirty: {
    status: false,
  },
  user: {
    firstTimeHere: true,
    onboardingStatus: "NOT_STARTED",
    stage: "WELCOME",
  },
  dataRecordSelection: null,
  playback: {
    status: false,
    currentFrame: null,
  },
  deleting: {
    status: false,
  },
  syncing: {
    status: false,
  },
  isLoading: false,
  saving: {
    status: false,
  },
  exporting: {
    status: false,
    dataRecords: [],
  },
};

const SessionContext = createContext<{
  state: SessionState;
  dispatch: React.Dispatch<SessionAction>;
}>({
  state: initialSessionState,
  dispatch: () => null,
});

const sessionReducer = (
  state: SessionState,
  action: SessionAction
): SessionState => {
  switch (action.type) {
    case "SET_DIRTY":
      return {
        ...state,
        dirty: {
          status: action.status,
          dataRecord: action.dataRecord,
          appRecord: action.appRecord,
        },
      };

    case "SET_USER":
      return {
        ...state,
        user: {
          firstTimeHere: action.firstTimeHere,
          onboardingStatus: action.onboardingStatus,
          stage: action.stage,
        },
      };

    case "SET_DATA_RECORD_SELECTION":
      return {
        ...state,
        dataRecordSelection: {
          record: action.record,
          frames: action.frames,
        },
      };

    case "CLEAR_DATA_RECORD_SELECTION":
      return {
        ...state,
        dataRecordSelection: null,
      };

    case "SET_PLAYBACK":
      return {
        ...state,
        playback: {
          status: action.status,
          currentFrame: action.currentFrame,
        },
      };

    case "SET_DELETING":
      return {
        ...state,
        deleting: {
          status: action.status,
          dataRecord: action.dataRecord,
        },
      };

    case "SET_SYNCING":
      return {
        ...state,
        syncing: {
          status: action.status,
          dataRecord: action.dataRecord,
        },
      };

    case "SET_LOADING":
      return {
        ...state,
        isLoading: action.status,
      };

    case "SET_SAVING":
      return {
        ...state,
        saving: {
          status: action.status,
        },
      };

    case "SET_EXPORTING":
      return {
        ...state,
        exporting: {
          status: action.status,
          dataRecords: action.dataRecords,
        },
      };

    default:
      return state;
  }
};

export const SessionProvider: React.FC<{ children: React.ReactNode, firstTime: boolean }> = ({
  children,
  firstTime
}) => {
  const [state, dispatch] = useReducer(sessionReducer, initialSessionState);

  useEffect(() => {
    if (firstTime) {
      dispatch({
        type: "SET_USER",
        firstTimeHere: true,
        onboardingStatus: "NOT_STARTED",
        stage: "WELCOME",
      });
    }
  }, []);

  
  return (
    <SessionContext.Provider value={{ state, dispatch }}>
      {children}
    </SessionContext.Provider>
  );
};

export const useSessionContext = () => useContext(SessionContext);
