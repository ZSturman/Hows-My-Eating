import usePersistedState from "./hooks/usePersistedState";
import { ImportDataButton } from "./components/ImportDataButton";
import ImportedDataList from "./components/ImportedDataList";
import "./App.css";
import SelectedDataRecord from "./components/SelectedDataRecord";
import { AppProvider } from "./context/AppProvider";
import { useEffect, useState } from "react";
import DemoView from "./components/DemoView/DemoView";
import { invoke } from '@tauri-apps/api/tauri';

const App: React.FC = () => {
  
  useEffect(() => {
    async function pingDatabase() {
      try {
        const response = await invoke('ping_mongodb');
        console.log(response);
      } catch (error) {
        console.error('Error pinging MongoDB:', error);
      }
    }

    pingDatabase();
  }, []);

  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
};

export default App;

const AppContent: React.FC = () => {
  const { isLoaded } = usePersistedState();
  const [showImports, setShowImports] = useState(false);
  const [demoMode, setDemoMode] = useState(true);

  if (!isLoaded) {
    return <div>Loading...</div>;
  }

  const toggleShowImports = () => {
    setShowImports(!showImports);
  };

  if (demoMode) {
    return (
      <div className="max-w-screen-xl h-full w-full flex mx-auto  items-center justify-center">
        
 <button
            onClick={() => setDemoMode(false)}
            className="border-2 rounded-md text-white bg-black absolute top-0 right-0"
          >
            Exit Demo Mode
          </button> 
          <div className="w-full ">
            <DemoView />
          </div>

      </div>
    );
  }

  return (
    <div className="p-2 w-screen h-screen flex-row flex">
      {showImports && (
        <div>
          <ImportDataButton />
          <ImportedDataList />
        </div>
      )}
      <div className="w-full relative">
        <div className="absolute top-0 left-0">
          <button
            className="border-2 rounded-md text-white bg-black"
            onClick={toggleShowImports}
          >
            {showImports ? "Hide Imports" : "Show Imports"}
          </button>

          <button
            className="border-2 rounded-md text-white bg-black"
            onClick={() => setDemoMode(true)}
          >
            Demo Mode
          </button>
        </div>

        <SelectedDataRecord />
      </div>
    </div>
  );
};
