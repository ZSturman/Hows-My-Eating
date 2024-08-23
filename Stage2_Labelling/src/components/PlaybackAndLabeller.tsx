import React, { useState, useEffect, useRef } from "react";
import Labeller from "./Labeller";
import VideoPlayer from "./VideoPlayer";
import Timeline from "./Timeline";
import { checkRequiredFiles } from "../utils/import";
import { parseLabelData, parseMotionData } from "../utils/readJson";
import ReactPlayer from "react-player";

type PlaybackAndLabellerProps = {
  selectedDataPath: string;
};

const PlaybackAndLabeller: React.FC<PlaybackAndLabellerProps> = ({ selectedDataPath }) => {
  const [movPath, setMovPath] = useState<string | null>(null);
  const [motionData, setMotionData] = useState<MotionData[] | null>(null);
  const [labelData, setLabelData] = useState<LabelledData[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [isPlaying, setIsPlaying] = useState(false);
  const [played, setPlayed] = useState(0);
  const [duration, setDuration] = useState(0);

  const playerRef = useRef<ReactPlayer>(null);

  useEffect(() => {
    const processFiles = async () => {
      try {

        if (typeof selectedDataPath !== "string" || !selectedDataPath.trim()) {
            setError("Invalid directory path.");
            return;
          }

        const { hasJson, hasMov, hasCsv } = await checkRequiredFiles(selectedDataPath);
        
        console.log("File Check:", { hasJson, hasMov, hasCsv }); // Add logging
  
        if (!hasJson || !hasMov) {
          setError("Directory must contain both a .mov file and a .json file.");
          return;
        }
  
        if (hasJson) {
          const motionFilePath = `${selectedDataPath}/${hasJson}`;
          console.log("Motion File Path:", motionFilePath); // Log the file path
          const motionData = await parseMotionData(motionFilePath);
          if (motionData) {
            setMotionData(motionData);
          } else {
            setError("Failed to parse motion data.");
          }
        }
  
        if (hasMov) {
          const movFilePath = `${selectedDataPath}/${hasMov}`;
          console.log("MOV File Path:", movFilePath); // Log the file path
          setMovPath(movFilePath);
        }
  
        if (hasCsv) {
          const labelFilePath = `${selectedDataPath}/${hasCsv}`;
          console.log("Label File Path:", labelFilePath); // Log the file path
          const labelData = await parseLabelData(labelFilePath);
          if (labelData) {
            setLabelData(labelData);
          } else {
            setError("Failed to parse label data.");
          }
        }
      } catch (err) {
        console.error(err);
        setError("An error occurred while processing files.");
      } finally {
        setLoading(false);
      }
    };
  
    processFiles();
  }, [selectedDataPath]);
  

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handleSeekChange = (newPlayed: number) => {
    setPlayed(newPlayed);
    if (playerRef.current) {
      playerRef.current.seekTo(newPlayed);
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>{error}</div>;
  }

  return (
    <div>

      {movPath && (
        <>
          <VideoPlayer
            videoPath={movPath}
            playing={isPlaying}
            played={played}
            onPlayPause={handlePlayPause}
            onSeekChange={handleSeekChange}
            onDuration={setDuration}
            ref={playerRef}
          />
          <Timeline
            played={played}
            duration={duration}
            onSeekChange={handleSeekChange}
          />
        </>
      )}
      <Labeller labelData={labelData} />
    </div>
  );
};

export default PlaybackAndLabeller;


{/* <MotionPlayer
data={motionData}
playing={isPlaying}
played={played}
onPlayPause={handlePlayPause}
duration={duration}
/>  */}