import { useEffect, useRef, useState } from "react";
import Canvases from "./Canvases";
import VideoPlayback from "./VideoPlayer";
import PlaybackControls from "./PlaybackControls";
import PieChartPlayback from "./PieChartPlayback";
import { defaultCanvas1A, defaultCanvas1B } from "./defaultCanvas";
import axios from 'axios';



type Label = {
  isEating: boolean;
  isTalking: boolean;
  mouthState: MouthState; 
  mouthAction: MouthAction; 
  primaryBodyState: PrimaryBodyState; 
  otherLabels: string[]; 
};

type LabelledMarker = Label & {
  timestamp: number;
};


const DemoView = () => {
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1);
  const [canvasesWithPoints, setCanvasesWithPoints] = useState<
    CanvasWithPoints[]
  >([defaultCanvas1A, defaultCanvas1B]);
  
  const [masterTimestamp, setMasterTimestamp] = useState<number>(0); // Master timestamp state
  const videoRef1 = useRef<VideoPlaybackHandle>(null);
  const videoRef2 = useRef<VideoPlaybackHandle>(null);


  const [markers, setMarkers] = useState<LabelledMarker[]>([]);
  const handleAddMarker = async (type: Label) => {
    const marker = { timestamp: masterTimestamp, ...type };
    await axios.post('http://localhost:5000/markers', marker);
    setMarkers([...markers, marker]);
  };
  
  useEffect(() => {
    const fetchMarkers = async () => {
      const response = await axios.get('http://localhost:5000/markers');
      setMarkers(response.data);
    };
    fetchMarkers();
  }, []);

  const handleFrameChange = (frames: number) => {
    const fps = 30; // Frames per second for video
    const newTimestamp = masterTimestamp + frames / fps;
    setMasterTimestamp(Math.max(0, newTimestamp));
  };


  const handlePlayPause = () => {
    if (isPlaying) {
      videoRef1.current?.pauseAllVideos();
      videoRef2.current?.pauseAllVideos();
    } else {
      videoRef1.current?.playAllVideos();
      videoRef2.current?.playAllVideos();
    }
    setIsPlaying(!isPlaying);
  };

  useEffect(() => {
    // Update the playback speed of all videos
    videoRef1.current?.setPlaybackSpeedForAll(playbackSpeed);
    videoRef2.current?.setPlaybackSpeedForAll(playbackSpeed);
  }, [playbackSpeed]);

  return (
    <div className="shadow-lg rounded-b-lg w-full h-full flex items-center justify-center overflow-hidden">
      <div className="rounded-lg shadow-lg bg-zinc-200 h-full w-full">
        <div className="flex flex-row justify-center ">
          <div className="flex flex-col">
            <VideoPlayback ref={videoRef1} />

            <PlaybackControls
              isPlaying={isPlaying}
              handlePlayPause={handlePlayPause}
              handleFrameChange={handleFrameChange}
              setPlaybackSpeed={setPlaybackSpeed}
              playbackSpeed={playbackSpeed}
              videoRef1={videoRef1}
              videoRef2={videoRef2}
              setMasterTimestamp={setMasterTimestamp}
            />
          </div>
          <div className=" h-full m-auto">
            <PieChartPlayback
              ref={videoRef2}
              isPlaying={isPlaying}
              masterTimestamp={masterTimestamp}
            />
          </div>
        </div>
        <div className="border-2 rounded-lg border-zinc-400 bg-zinc-100  m-2">
          <Canvases
            canvasesWithPoints={canvasesWithPoints}
            setCanvasesWithPoints={setCanvasesWithPoints}
          />
        </div>
      </div>
    </div>
  );
};

export default DemoView;
