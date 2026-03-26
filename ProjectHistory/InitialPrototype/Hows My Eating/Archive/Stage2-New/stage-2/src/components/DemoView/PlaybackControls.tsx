import { useEffect } from "react";
import { FaPause, FaPlay } from "react-icons/fa";
import { MdOutlineArrowForwardIos, MdOutlineArrowBackIos } from "react-icons/md";
import { RiSpeedUpFill } from "react-icons/ri";

// Use the custom ref type
type PlaybackControlsProps = {
  handlePlayPause: () => void;
  isPlaying: boolean;
  handleFrameChange: (frames: number) => void;
  setPlaybackSpeed: (speed: number) => void;
  playbackSpeed: number;
  videoRef1: React.RefObject<VideoPlaybackHandle>;
  videoRef2: React.RefObject<VideoPlaybackHandle>;
  setMasterTimestamp: React.Dispatch<React.SetStateAction<number>>; 
};

const PlaybackControls: React.FC<PlaybackControlsProps> = ({
  handlePlayPause,
  isPlaying,
  handleFrameChange,
  setPlaybackSpeed,
  playbackSpeed,
  videoRef1,
  videoRef2,
  setMasterTimestamp,
}) => {

  useEffect(() => {
    let intervalId: NodeJS.Timeout | undefined; // Initialize as possibly undefined

    if (isPlaying) {
      // Update masterTimestamp every 0.2 seconds (200 ms) while playing
      intervalId = setInterval(() => {
        setMasterTimestamp((prevTimestamp: number) => prevTimestamp + 0.2);
      }, 200);
    } else if (intervalId) {
      // Clear the interval when paused
      clearInterval(intervalId);
    }

    // Clean up the interval when the component unmounts or when isPlaying changes
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [isPlaying, setMasterTimestamp]);


  const handlePlaybackSpeedChange = () => {
    const currentIndex = playBackSpeeds.indexOf(playbackSpeed);
    const nextIndex = (currentIndex + 1) % playBackSpeeds.length;
    const newSpeed = playBackSpeeds[nextIndex];
    setPlaybackSpeed(newSpeed);
    videoRef1.current?.setPlaybackSpeedForAll(newSpeed);
    videoRef2.current?.setPlaybackSpeedForAll(newSpeed);
  };

  const playBackSpeeds = [0.1, 0.25, 0.5, 0.75, 1];



  return (
    <div className="flex flex-row items-center justify-center w-full gap-4 mb-4">
      {/* Skip backward by 30 frames */}
      <button
        className="text-3xl hover:scale-105 hover:opacity-70 flex flex-row"
        onClick={() => handleFrameChange(-30)}
      >
        <div className="-mr-5">
          <MdOutlineArrowBackIos />
        </div>
        <div>
          <MdOutlineArrowBackIos />
        </div>
      </button>

      {/* Skip backward by 1 frame */}
      <button
        className="text-3xl hover:scale-105 hover:opacity-70"
        onClick={() => handleFrameChange(-1)}
      >
        <MdOutlineArrowBackIos />
      </button>

      {/* Play/Pause Button */}
      <button
        onClick={handlePlayPause}
        className="text-5xl px-4 hover:scale-105 hover:opacity-70"
      >
        {isPlaying ? <FaPause /> : <FaPlay />}
      </button>

      {/* Skip forward by 1 frame */}
      <button
        className="text-3xl hover:scale-105 hover:opacity-70"
        onClick={() => handleFrameChange(1)}
      >
        <MdOutlineArrowForwardIos />
      </button>

      {/* Skip forward by 30 frames */}
      <button
        className="text-3xl hover:scale-105 hover:opacity-70 flex flex-row"
        onClick={() => handleFrameChange(30)}
      >
        <div>
          <MdOutlineArrowForwardIos />
        </div>
        <div className="-ml-5">
          <MdOutlineArrowForwardIos />
        </div>
      </button>

      {/* Playback Speed Button */}
      <button
        className="p-2 rounded flex items-center hover:scale-105 hover:opacity-70"
        onClick={handlePlaybackSpeedChange}
      >
        <RiSpeedUpFill className="mr-2" />
        {playbackSpeed}x
      </button>
    </div>
  );
};

export default PlaybackControls;