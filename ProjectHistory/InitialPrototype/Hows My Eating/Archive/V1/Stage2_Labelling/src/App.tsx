import { useEffect } from "react";
import { AppContextProvider } from "./context/AppContext";
import { useToast } from "./hooks/use-toast";
import Sidebar from "./components/Sidebar";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "./components/ui/resizable";
import DefaultWelcomeScreen from "./components/DefaultWelcomeScreen";
import SelectedDataDashboard from "./components/SelectedDataDashboard";
import {
  ChewingDataContextProvider,
  useChewingDataContext,
} from "./context/ChewingDataContextProvider";
import { useLog } from "./hooks/useLog";
import { LoaderCircle } from "lucide-react";
import { Button } from "./components/ui/button";
import { ArrowBigLeft } from "lucide-react";

type ShowToastMessageProps = {
  logEntry: LogEntry;
};

const ShowToastMessage: React.FC<ShowToastMessageProps> = ({ logEntry }) => {
  const { toast } = useToast();

  useEffect(() => {
    if (logEntry.type === "ERROR") {
      toast({
        title: "Error",
        description: logEntry.message,
        variant: "destructive",
      });
    } else {
      toast({
        title: "Info",
        description: logEntry.message,
      });
    }
  }, [logEntry, toast]);

  return null;
};

const MainContent = () => {
  const { toastMessage } = useLog();
  const {
    selectedData,
    processing,
    setSelectedData,
    selectedArchivedData,
    setSelectedArchivedData,
  } = useChewingDataContext();

  const handleBackClicked = () => {
    setSelectedData(null);
    setSelectedArchivedData(null);
  };

  return (
    <div className="w-screen h-screen">
      {processing && (
        <div className="absolute top-0 left-0 w-full flex items-center justify-center">
          <div className="p-4 rounded-md flex flex-row items-center gap-4">
            <h1 className="text-lg">Processing data...</h1>
            <LoaderCircle className="animate-spin h-8 w-8" />
          </div>
        </div>
      )}

      {toastMessage && <ShowToastMessage logEntry={toastMessage} />}

      <ResizablePanelGroup direction="horizontal" className="w-full h-full">
        <ResizablePanel defaultSize={20} className="min-w-[200px] max-w-[50vw]">
          <Sidebar />
        </ResizablePanel>
        <ResizableHandle />
        <ResizablePanel>

 

          
          {selectedData && (
            <div>
              <Button onClick={handleBackClicked}>
                <ArrowBigLeft size={24} />
              </Button>
              <SelectedDataDashboard  />
            </div>
          )}
          {selectedArchivedData && (
            <div>
              <Button onClick={handleBackClicked}>
                <ArrowBigLeft size={24} />
              </Button>
              <SelectedDataDashboard  />
            </div>
          )}



          {!selectedData && !selectedArchivedData && <DefaultWelcomeScreen />}
     
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <AppContextProvider>
      <ChewingDataContent>
        <MainContent />
      </ChewingDataContent>
    </AppContextProvider>
  );
};

export default App;

const ChewingDataContent: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  return <ChewingDataContextProvider>{children}</ChewingDataContextProvider>;
};
