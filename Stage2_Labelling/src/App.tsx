import { useState } from "react";
import "./App.css";
import ImportedDataDirectories from "./components/ImportedDataDirectories";
import PlaybackAndLabeller from "./components/PlaybackAndLabeller";
import { handleOpenFileDialog } from "./utils/import";
import TrackingJson from "./components/TrackingJson";

function App() {
  const [selectedDataPath, setSelectedDataPath] = useState<string | null>(null);
  const [messages, setMessages] = useState<FlashMessage[]>([]);
  const [showSidebar, setShowSidebar] = useState(true);
  const [showTrackingJson, setShowTrackingJson] = useState(false);

  return (
    <div className="flex flex-col bg-zinc-900 w-screen h-screen text-zinc-300">
      <div className="w-full bg-slate-800 flex flex-row p-1">
        <button onClick={() => setShowSidebar(!showSidebar)} className=" p-2">
          {showSidebar ? "|<" : ">|"}
        </button>
        <button onClick={() => setShowTrackingJson(!showTrackingJson)} className=" p-2">
          {showTrackingJson ? "|<" : ">|"}
        </button>

        <button
          onClick={() => handleOpenFileDialog(setMessages)}
          className="bg-slate-800 text-zinc-300 p-2"
        >
          Import
        </button>
      </div>

      <div>
        <h1 className="text-2xl">How's my eating?: Data Labelling</h1>
        {messages.length > 0 && (
          <div className="mt-2 text-red-500">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={
                  "mb-2" +
                  (msg.type === "error"
                    ? " text-red-500"
                    : msg.type === "success"
                    ? "text-green-500"
                    : msg.type === "warning"
                    ? "text-yellow-500"
                    : "")
                }
              >
                {msg.message}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="flex flex-row h-full">
        {showSidebar && (
          <div className="h-full border-r-2 text-nowrap">
            <ImportedDataDirectories
              setSelectedDataPath={setSelectedDataPath}
            />
          </div>
        )}
      <div className="flex flex-row h-full">
        {selectedDataPath && showTrackingJson && (
            <div className="h-full border-r-2 text-nowrap px-5">
            <TrackingJson selectedDataPath={selectedDataPath}  />
            </div>
            )}
            </div>


        <div className="w-full">
          {selectedDataPath && (
            <PlaybackAndLabeller selectedDataPath={selectedDataPath} />
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
