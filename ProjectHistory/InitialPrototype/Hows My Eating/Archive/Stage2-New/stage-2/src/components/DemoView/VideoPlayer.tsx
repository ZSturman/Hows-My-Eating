import { resolveResource } from "@tauri-apps/api/path";
import { convertFileSrc } from "@tauri-apps/api/tauri";
import {
  useEffect,
  useRef,
  useState,
  forwardRef,
  useImperativeHandle,
} from "react";

const VideoPlayback = forwardRef<VideoPlaybackHandle>((_, ref) => {
  const playerRefs = {
    combinedOutput: useRef<HTMLVideoElement | null>(null),
    lipsVideo: useRef<HTMLVideoElement | null>(null),
    jawlineVideo: useRef<HTMLVideoElement | null>(null),
    handVideo: useRef<HTMLVideoElement | null>(null),
  };

  const [videoSources, setVideoSources] = useState({
    combinedOutput:
      "/Users/zacharysturman/Desktop/Stage2-New/stage-2/public/demo/combined_output.webm",
    lipsVideo:
      "/Users/zacharysturman/Desktop/Stage2-New/stage-2/public/demo/lips_points.webm",
    jawlineVideo:
      "/Users/zacharysturman/Desktop/Stage2-New/stage-2/public/demo/jawline_points.webm",
    handVideo:
      "/Users/zacharysturman/Desktop/Stage2-New/stage-2/public/demo/hand_outline.webm",
  });

  useEffect(() => {
    const controller = new AbortController();
    const { signal } = controller;

    const getCorrectSource = async () => {
      await resolveResource(videoSources.combinedOutput);
      await resolveResource(videoSources.lipsVideo);
      await resolveResource(videoSources.jawlineVideo);
      await resolveResource(videoSources.handVideo);
      try {
        if (!signal.aborted) {
          const combinedOutput = convertFileSrc(videoSources.combinedOutput);
          const lipsVideo = convertFileSrc(videoSources.lipsVideo);
          const jawlineVideo = convertFileSrc(videoSources.jawlineVideo);
          const handVideo = convertFileSrc(videoSources.handVideo);

          setVideoSources({ combinedOutput, lipsVideo, jawlineVideo, handVideo });
        }
      } catch (error: any) {
        if (error.name !== "AbortError") {
          console.error("Error fetching path:", error);
        }
      }
    };

    getCorrectSource();

    return () => {
      controller.abort();
    };
  }, []);

  useImperativeHandle(ref, () => ({
    playAllVideos: () => {
      Object.values(playerRefs).forEach((ref) => {
        ref.current?.play();
      });
    },
    pauseAllVideos: () => {
      Object.values(playerRefs).forEach((ref) => {
        ref.current?.pause();
      });
    },
    setPlaybackSpeedForAll: (speed: number) => {
      Object.values(playerRefs).forEach((ref) => {
        if (ref.current) {
          ref.current.playbackRate = speed;
        }
      });
    },
    changeFrameForAll: (frames: number) => {
      Object.values(playerRefs).forEach((ref) => {
        if (ref.current) {
          const fps = 30;
          const newTime = ref.current.currentTime + frames / fps;
          ref.current.currentTime = Math.max(0, newTime);
        }
      });
    },
    syncAllVideosTo: (timestamp: number) => { // Implement the syncAllVideosTo method
      Object.values(playerRefs).forEach((ref) => {
        if (ref.current) {
          ref.current.currentTime = timestamp;
        }
      });
    },
    playerRefs,
  }));

  const smallerVidWidthAndHeight = "150px";

  return (
    <div className="flex flex-row items-center justify-center w-full p-8 gap-2">
      <div className="relative w-[500px] h-[500px] bg-gray-800 rounded-lg shadow-lg overflow-hidden">
        <video
          ref={playerRefs.combinedOutput as React.RefObject<HTMLVideoElement>}
          src={videoSources.combinedOutput}
          width="100%"
          height="100%"
        />
      </div>
        <div className="h-full flex flex-col justify-between gap-6">
          {[
            {
              ref: playerRefs.lipsVideo,
              url: videoSources.lipsVideo,
              label: "Mouth",
            },
            {
              ref: playerRefs.jawlineVideo,
              url: videoSources.jawlineVideo,
              label: "Jawline",
            },
            {
              ref: playerRefs.handVideo,
              url: videoSources.handVideo,
              label: "Hand",
            },
          ].map((video, idx) => (
            <div
              key={idx}
              className="flex flex-col items-center justify-center rounded-lg shadow-lg overflow-hidden"
            >
              <div className="object-cover w-full h-full rounded-lg relative">
                <div className="w-full text-center absolute top-0 left-0 text-white">
                  {video.label}
                </div>
                <video
                  ref={video.ref as React.RefObject<HTMLVideoElement>}
                  src={video.url}
                  width={smallerVidWidthAndHeight}
                  height={smallerVidWidthAndHeight}
                  className="rounded-lg"
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }
);

export default VideoPlayback;
