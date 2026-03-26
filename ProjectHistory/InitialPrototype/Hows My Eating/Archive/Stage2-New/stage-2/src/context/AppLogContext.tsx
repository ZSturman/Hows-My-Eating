import React, {
  createContext,
  useReducer,
  useContext,
  ReactNode,
  Dispatch,
} from "react";

type LoggerActions =
  | "ERROR"
  | "SUCCESS"
  | "INFO"
  | "WARNING"
  | "STATUS"
  | "CLEAR";

export type AppLog = {
  payload?: any;
  flash?: boolean;
  timestamp: number;
  message: string;
  status: LoggerActions;
};

type AppLogs = {
  logs: AppLog[];
};

const defaultLog: AppLog = {
  timestamp: Date.now(),
  message: "",
  status: "CLEAR",
  flash: false,
};

const initialAppLogState: AppLogs = {
  logs: [defaultLog],
};

const AppLogContext = createContext<{
  state: AppLogs;
  dispatch: Dispatch<AppLog>;
}>({
  state: initialAppLogState,
  dispatch: () => null,
});

const logReducer = (state: AppLogs, action: AppLog): AppLogs => {
  switch (action.status) {
    case "ERROR":
      state.logs.push(action);
      return state;
    case "SUCCESS":
      state.logs.push(action);
      return state;
    case "INFO":
      state.logs.push(action);
      return state;
    case "WARNING":
      state.logs.push(action);
      return state;
    case "STATUS":
      state.logs.push(action);
      return state;
    case "CLEAR":
      state.logs = [];
      return state;
    default:
      return state;
  }
};
export const AppLogProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const [state, dispatch] = useReducer(logReducer, initialAppLogState);
  return (
    <AppLogContext.Provider value={{ state, dispatch }}>
      {children}
    </AppLogContext.Provider>
  );
};

export const useAppLogContext = () => useContext(AppLogContext);
