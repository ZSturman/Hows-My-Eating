import { useState } from "react";
import { open } from "@tauri-apps/api/dialog";
import { exists, BaseDirectory } from "@tauri-apps/api/fs";
import { homeDir } from "@tauri-apps/api/path";
import "./App.css";
import VideoPlayer from "./components/VideoPlayer";
import ImportedFiles from "./components/ImportedFiles";

function App() {
  const [selectedFile, setSelectedFile] = useState<string | string[] | null>(
    null
  );
  const [importedFiles, setImportedFiles] = useState<string[]>([]);
  const [playbackVideo, setPlaybackVideo] = useState<string | null>(null);
  const [message, setMessage] = useState("No updates yet...");

  async function checkFileExists(filePath: string): Promise<boolean> {
    console.log("Checking file exists:", filePath);
    return await exists(filePath, { dir: BaseDirectory.Home });
  }

  const handleOpenFileDialog = async () => {
    const selectedFile = await open({
      multiple: true,
      defaultPath: await homeDir(),
      filters: [
        {
          name: "Video file",
          extensions: ["mp4", "avi", "mov", "wmv", "mkv"],
        },
      ],
    });
    if (selectedFile) {
      setSelectedFile(selectedFile);
      let newFiles = [];

      if (Array.isArray(selectedFile)) {
        // check if all files exist
        const fileExists = await Promise.all(selectedFile.map(checkFileExists));
        if (fileExists.includes(false)) {
          setMessage("Some files do not exist");
          return;
        } else {
          // add all files to importedFiles without duplicates
          newFiles = selectedFile.filter(
            (file) => !importedFiles.includes(file)
          );
        }
      } else {
        const fileExists = await checkFileExists(selectedFile);
        if (!fileExists) {
          setMessage("File does not exist");
          return;
        } else {
          newFiles = [selectedFile];
        }
      }

      const updatedImportedFiles = [...importedFiles, ...newFiles];
      setImportedFiles(updatedImportedFiles);
      setPlaybackVideo(updatedImportedFiles[0]);

      console.log("Updated imported files:", updatedImportedFiles);
      console.log("Playback video set to:", updatedImportedFiles[0]);

      setMessage(
        `File(s) imported successfully. Total files: ${updatedImportedFiles.length}. Selected file: ${selectedFile}, Playback video: ${updatedImportedFiles[0]}`
      );
    }
  };

  return (
    <div className="flex flex-col bg-zinc-900 w-screen h-screen text-zinc-300">
      <div>
        <h1 className="text-2xl">Stage 2: Label</h1>
        <p>{message}</p>
      </div>

      <div className="flex flex-row h-full">
        <div className="h-full border-r-2 text-nowrap">
          <button className="bg-zinc-500 rounded-md p-2" onClick={handleOpenFileDialog}>Select Input File</button>


          <ImportedFiles importedFiles={importedFiles}/>
        </div>
        <div className="w-full">{playbackVideo && <VideoPlayer videoPath={playbackVideo} />}</div>
      </div>
    </div>
  );
}

export default App;
