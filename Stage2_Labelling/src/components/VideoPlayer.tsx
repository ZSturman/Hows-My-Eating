import { useState, useEffect, useRef } from "react";
import ReactPlayer from "react-player";
import "tailwindcss/tailwind.css";
import { convertFileSrc } from "@tauri-apps/api/tauri";
import Timeline from "./Timeline";

type VideoPlayerProps = {
    videoPath: string;
};

const VideoPlayer: React.FC<VideoPlayerProps> = ({ videoPath }) => {
    const [playing, setPlaying] = useState(false);
    const [played, setPlayed] = useState(0);
    const [duration, setDuration] = useState(0);
    const playerRef = useRef<ReactPlayer>(null);

    useEffect(() => {
        console.log("Video path received in VideoPlayer:", videoPath);
    }, [videoPath]);

    const handlePlayPause = () => {
        setPlaying(!playing);
    };

    const handleSeekChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setPlayed(parseFloat(e.target.value));
    };

    const handleFastForward = () => {
        if (playerRef.current) {
            const currentTime = playerRef.current.getCurrentTime();
            const duration = playerRef.current.getDuration();
            const newTime = currentTime + 10; // Fast forward by 10 seconds
            if (newTime <= duration) {
                playerRef.current.seekTo(newTime);
            }
        }
    };

    const handleRewind = () => {
        if (playerRef.current) {
            const currentTime = playerRef.current.getCurrentTime();
            const newTime = currentTime - 10; // Rewind by 10 seconds
            if (newTime >= 0) {
                playerRef.current.seekTo(newTime);
            }
        }
    };

    // Convert the file path to a Tauri-compatible URL
    const tauriVideoPath = convertFileSrc(videoPath);

    return (
        <div className="flex flex-col items-center justify-center p-4">
            <ReactPlayer
                ref={playerRef}
                url={tauriVideoPath}
                playing={playing}
                controls={false}
                onProgress={(state) => setPlayed(state.played)}
                onDuration={(duration) => setDuration(duration)}
                style={{ maxWidth: "300px", maxHeight: "200px", backgroundColor: "black" }}
            />

            <Timeline />

            <div className="flex items-center justify-between w-full mt-2">
                <button
                    className="bg-blue-500 text-white px-4 py-2 rounded"
                    onClick={handlePlayPause}
                >
                    {playing ? "Pause" : "Play"}
                </button>
                <button
                    className="bg-blue-500 text-white px-4 py-2 rounded"
                    onClick={handleRewind}
                >
                    Rewind
                </button>
                <button
                    className="bg-blue-500 text-white px-4 py-2 rounded"
                    onClick={handleFastForward}
                >
                    Fast Forward
                </button>
                <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.01"
                    value={played}
                    onChange={handleSeekChange}
                    className="w-full mx-2"
                />
                <div>
                    {Math.round(played * duration)} / {Math.round(duration)} sec
                </div>
            </div>
        </div>
    );
};

export default VideoPlayer;