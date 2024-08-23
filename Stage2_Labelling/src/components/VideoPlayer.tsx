import { forwardRef } from "react";
import ReactPlayer from "react-player";
import "tailwindcss/tailwind.css";
import { convertFileSrc } from "@tauri-apps/api/tauri";

type VideoPlayerProps = {
  videoPath: string;
  playing: boolean;
  played: number;
  onPlayPause: () => void;
  onSeekChange: (newPlayed: number) => void;
  onDuration: (duration: number) => void;
};

const VideoPlayer = forwardRef<ReactPlayer, VideoPlayerProps>(
  ({ videoPath, playing, played, onPlayPause, onSeekChange, onDuration }, ref) => {
    const tauriVideoPath = convertFileSrc(videoPath);

    return (
      <div className="flex flex-col items-center justify-center p-4">
        <ReactPlayer
          ref={ref}
          url={tauriVideoPath}
          playing={playing}
          controls={false}
          onProgress={(state) => onSeekChange(state.played)}
          onDuration={onDuration}
          style={{ maxWidth: "300px", maxHeight: "200px", backgroundColor: "black" }}
        />
        <div className="flex items-center justify-between w-full mt-2">
          <button
            className="bg-blue-500 text-white px-4 py-2 rounded"
            onClick={onPlayPause}
          >
            {playing ? "Pause" : "Play"}
          </button>
        </div>
      </div>
    );
  }
);

export default VideoPlayer;
