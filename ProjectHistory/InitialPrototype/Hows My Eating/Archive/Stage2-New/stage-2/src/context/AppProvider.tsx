import { AppLogProvider } from "./AppLogContext";
import { DataRecordProvider } from "./DataRecordContext";
import { ImportProvider } from "./ImportContext";
import { SessionProvider } from "./SessionContext";
import { AppRecordProvider } from "./AppRecordContext";
import usePersistedState from "../hooks/usePersistedState";
import { KeyboardProvider } from "./KeyboardContext";

export const AppProvider: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {
  const { appRecord } = usePersistedState();

  return (
    <KeyboardProvider>
      <SessionProvider firstTime={appRecord ? true : false}>
        <AppRecordProvider>
          <DataRecordProvider>
            <ImportProvider>
              <AppLogProvider>{children}</AppLogProvider>
            </ImportProvider>
          </DataRecordProvider>
        </AppRecordProvider>
      </SessionProvider>
    </KeyboardProvider>
  );
};
