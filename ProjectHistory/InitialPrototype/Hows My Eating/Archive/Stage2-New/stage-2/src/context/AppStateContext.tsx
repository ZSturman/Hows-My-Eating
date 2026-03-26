// import React, {
//   createContext,
//   useReducer,
//   useContext,
//   ReactNode,
//   Dispatch,
//   useEffect,
// } from "react";
// import usePersistedState from "../hooks/usePersistedState";
// import {
//   saveLogsToFile,
//   exportAppRecordToFile,
// } from "../handlers/appRecordFileHandler";


// import { resourceDir } from '@tauri-apps/api/path';
// import { deleteDataFromAppData } from "../utils/deleteDataRecords";




// // Define actions for reducer


// // Reducer function to handle actions
// const appReducer = (state: AppState, action: AppRecordAction): AppState => {
//   console.log("Reducer action received:", action);
//   switch (action.type) {
//     case FIRST_TIME_HERE:
//       console.log("Setting initial state for FIRST_TIME_HERE");
//       return {
//         appRecord: {
//           firstOpened: Date.now(),
//           lastOpened: Date.now(),
//           dataDirectories: [],
//           importDirectory: "",
//           exportDirectory: "",
//         },
//         sessionState: initialSessionState,
//       };
//     // case WELCOME_BACK:
//     //   console.log("Updating state for WELCOME_BACK:", action.payload);
//     //   return {
//     //     appRecord: { ...action.payload.appRecords },
//     //     sessionState: { ...action.payload.sessionState },
//     //   };
//     case IS_IMPORTING:
//       console.log("Updating state for IMPORTING_DATA");
//       return {
//         ...state,
//         sessionState: { ...state.sessionState, isImporting: true },
//       };
//     case IMPORT_CANCELLED:
//       console.log("Updating state for IMPORT_CANCELLED");
//       return {
//         ...state,
//         sessionState: { ...state.sessionState, isImporting: false },
//       };
//     case IMPORT_COMPLETE:
//       console.log("Updating state for IMPORT_COMPLETE", action.payload);
//       return {
//         ...state,
//         sessionState: {
//           ...state.sessionState,
//           isImporting: false,
//           isDirty: true,
//         },
//         appRecord: {
//           ...state.appRecord,
//           dataDirectories: [...state.appRecord.dataDirectories, ...action.payload],
//         },
//       };
//       case DELETING_DATA_RECORD:
//       console.log("Updating state for DELETING_DATA_RECORD", action.payload);
//       return {
//         ...state,
//         sessionState: {
//           ...state.sessionState,
//           isDeleting: true,
//           dataToDelete: action.payload,
//         },
//         appRecord: {
//           ...state.appRecord,
//           dataDirectories: state.appRecord.dataDirectories.filter(
//             (dir) => dir.id !== action.payload.id
//           ),
//         },
//       };
//       case DATA_RECORD_DELETED:
//       console.log("Updating state for DATA_RECORD_DELETED", action.payload);
//       return {
//         ...state,
//         sessionState: {
//           ...state.sessionState,
//           isDeleting: false,
//           isDirty: true,
//           dataToDelete: null,
//         },
//       };

//     case SET_SELECTED_DATA_RECORD:
//       console.log("Updating state for SET_SELECTED_DATA_RECORD", action.payload);
//       return {
//         ...state,
//         sessionState: {
//           ...state.sessionState,
//           selectedDataRecord: action.payload,
//         },
        
//       };

//       case SET_CHECKING_DATA_RECORD:
//       console.log("Updating state for SET_CHECKING_DATA_RECORD", action.payload);
//       return {
//         ...state,
//         sessionState: {
//           ...state.sessionState,
//           isCheckingDataRecord: action.payload,
//         },
//       };
//       case GETTING_SELECTED_DATA_FRAMES:
//       console.log("Updating state for GETTING_SELECTED_DATA_FRAMES", action.payload);
//       return {
//         ...state,
//         sessionState: {
//           ...state.sessionState,
//           selectedDataRecord: action.payload,
//           isCheckingDataRecord: true,
//         },
//       };

//     case APP_RECORD_SAVED:
//       console.log("Marking state as clean");
//       return {
//         ...state,
//         sessionState: {
//           ...state.sessionState,
//           isDirty: false,
//         },
//       };
//     default:
//       return state;
//   }
// };

// // Context for App Records and Session State
// const AppStateContext = createContext<{
//   state: AppState;
//   dispatch: Dispatch<AppRecordAction>;
//   isLoaded: boolean;
//   exportState: () => Promise<void>;
// }>({
//   state: initialAppState,
//   dispatch: () => undefined,
//   isLoaded: true,
//   exportState: async () => {},
// });

// // Provider Component
// export const AppStateProvider: React.FC<{
//   children: ReactNode;
//   currentState: AppState;
// }> = ({ children, currentState }) => {
//   const [state, dispatch] = useReducer(appReducer, currentState);

//   const { isLoaded } = usePersistedState();



//   useEffect(() => {

//     const getPaths = async () => {
//       const resourceDirPath = await resourceDir();
//       console.log("Resource Dir Path: ", resourceDirPath);
//     }
    
//     getPaths()
//   }, [])

//   useEffect(() => {
//     if (state.sessionState.isDirty) {
//       let saveTimeout: NodeJS.Timeout | null = null;

//       const syncStateAndFile = async () => {
//         if (state.sessionState.isDirty) {
//           // Debounce the save operation
//           if (saveTimeout) {
//             clearTimeout(saveTimeout);
//           }
//           saveTimeout = setTimeout(async () => {
//             await exportAppRecordToFile(state.appRecord);
//             console.log("State saved to file successfully");
//             dispatch({ type: APP_RECORD_SAVED });
//           }, 5000);
//         }
//       };
//       syncStateAndFile();
//     }
//   }, [state.sessionState.isDirty]);


//   useEffect(() => {
//     const deleteDataRecord = async () => {
//       if (state.sessionState.isDeleting) {
//         if (state.sessionState.dataToDelete) {
//           console.log("Deleting data record:", state.sessionState.dataToDelete);
//           const deletedDirectory = deleteDataFromAppData(state.sessionState.dataToDelete);
//           console.log("Deleted Directory: ", deletedDirectory);
//           dispatch({ type: DATA_RECORD_DELETED, payload: state.sessionState.dataToDelete });

//         }
        

//       }
//     };

//     deleteDataRecord();

//   }, [state.sessionState.isDeleting]);

//   useEffect(() => {

//     const checkDataRecord = async () => {
//       if (state.sessionState.isCheckingDataRecord) {
//         if (state.sessionState.selectedDataRecord) {
//           console.log("Checking data record:", state.sessionState.selectedDataRecord);
          
//         }
//       }
//     };

//     checkDataRecord();

//   }, [state.sessionState.isCheckingDataRecord]);

//   return (
//     <AppStateContext.Provider
//       value={{
//         state,
//         dispatch,
//         isLoaded,
//         exportState: async () => saveLogsToFile(state.sessionState.logger),
//       }}
//     >
//       {children}
//     </AppStateContext.Provider>
//   );
// };

// // Custom Hook to use the AppState
// export const useAppState = () => useContext(AppStateContext);
