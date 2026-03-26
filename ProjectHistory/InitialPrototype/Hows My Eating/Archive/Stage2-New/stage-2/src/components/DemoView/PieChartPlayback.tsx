import { resolveResource } from "@tauri-apps/api/path";
import { convertFileSrc } from "@tauri-apps/api/tauri";
import {
  useEffect,
  useRef,
  useState,
  forwardRef,
  useImperativeHandle,
} from "react";
import { useKeyboard } from "../../context/KeyboardContext";

const PieChartPlayback = forwardRef<VideoPlaybackHandle, { masterTimestamp: number, isPlaying: boolean }>((props, ref) => {
  const { masterTimestamp, isPlaying } = props; 
  const { pressedKeys } = useKeyboard();
  const [loading, setLoading] = useState(false);

  const playerRefs = {
    one: useRef<HTMLVideoElement | null>(null),
    two: useRef<HTMLVideoElement | null>(null),
    three: useRef<HTMLVideoElement | null>(null),
    four: useRef<HTMLVideoElement | null>(null),
    five: useRef<HTMLVideoElement | null>(null),
  };

  const [videoSources, setVideoSources] = useState({
    one: "/Users/zacharysturman/Desktop/Stage2-New/stage-2/public/demo/1.webm",
    two: "/Users/zacharysturman/Desktop/Stage2-New/stage-2/public/demo/2.webm",
    three: "/Users/zacharysturman/Desktop/Stage2-New/stage-2/public/demo/3.webm",
    four: "/Users/zacharysturman/Desktop/Stage2-New/stage-2/public/demo/4.webm",
    five: "/Users/zacharysturman/Desktop/Stage2-New/stage-2/public/demo/5.webm",
  });

  const [selectedVideo, setSelectedVideo] = useState<number>(1);

  useEffect(() => {
    const controller = new AbortController();
    const { signal } = controller;

    const getCorrectSource = async () => {
      await resolveResource(videoSources.one);
      await resolveResource(videoSources.two);
      await resolveResource(videoSources.three);
      await resolveResource(videoSources.four);
      await resolveResource(videoSources.five);
      try {
        if (!signal.aborted) {
          const one = convertFileSrc(videoSources.one);
          const two = convertFileSrc(videoSources.two);
          const three = convertFileSrc(videoSources.three);
          const four = convertFileSrc(videoSources.four);
          const five = convertFileSrc(videoSources.five);

          setVideoSources({ one, two, three, four, five });
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
    syncAllVideosTo: (timestamp: number) => {
      Object.values(playerRefs).forEach((ref) => {
        if (ref.current) {
          ref.current.currentTime = timestamp;
        }
      });
    },
    playerRefs,
  }));

  // Sync videos to master timestamp whenever it changes
  useEffect(() => {
    Object.values(playerRefs).forEach((ref) => {
      if (ref.current) {
        ref.current.currentTime = masterTimestamp;
      }
    });

    // Log the master timestamp
    console.log(`Master Timestamp: ${masterTimestamp}`);
  }, [masterTimestamp]);

  // Log the current video state whenever selected video changes
  useEffect(() => {
    const currentVideoRef = playerRefs[`one`]?.current;

    if (currentVideoRef) {
      console.log(`Current Video: Video ${selectedVideo}`);
      console.log(`Video State: ${currentVideoRef.paused ? 'Paused' : 'Playing'}`);
      console.log(`Video Element Class: ${selectedVideo === 1 ? "block" : "hidden"}`);
    }
  }, [selectedVideo]);

  useEffect(() => {
    if (!ref) return;
    if (pressedKeys.size > 0) {
      if (
        pressedKeys.has("1") ||
        pressedKeys.has("2") ||
        pressedKeys.has("3") ||
        pressedKeys.has("4") ||
        pressedKeys.has("5")
      ) {
        setLoading(true);
        setTimeout(() => {
          const currentTime = playerRefs[`one`]?.current?.currentTime || 0; // Use the first video's timestamp as reference

          if (pressedKeys.has("1")) {
            setSelectedVideo(1);
          } else if (pressedKeys.has("2")) {
            setSelectedVideo(2);
          } else if (pressedKeys.has("3")) {
            setSelectedVideo(3);
          } else if (pressedKeys.has("4")) {
            setSelectedVideo(4);
          } else if (pressedKeys.has("5")) {
            setSelectedVideo(5);
          }
          setLoading(false);

          // Log selected video and its state
          console.log(`Switched to Video ${selectedVideo}`);
          const videoElement = playerRefs[`one`]?.current;
          console.log(`Current Video State: ${videoElement?.paused ? 'Paused' : 'Playing'}`);

          // Type cast ref to MutableRefObject before accessing current
          (ref as React.MutableRefObject<VideoPlaybackHandle | null>).current?.syncAllVideosTo(currentTime);
        }, 200);
      }
    }
  }, [pressedKeys]);

  useEffect(() => {
    if (isPlaying) {
      Object.values(playerRefs).forEach((ref) => {
        ref.current?.play();
      });
    } else {
      Object.values(playerRefs).forEach((ref) => {
        ref.current?.pause();
      });
    }

  }, [selectedVideo])



  return (
    <div className="flex items-center justify-center ">
      <div className="overflow-hidden rounded-full">
        {loading ? (
          <svg
            className="animate-spin h-5 w-5 text-gray-900"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            ></circle>
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
            ></path>
          </svg>
        ) : (
          <div>
            <video
              ref={playerRefs.one as React.RefObject<HTMLVideoElement>}
              src={videoSources.one}
              width="100%"
              height="100%"
              className={`${selectedVideo === 1 ? "block" : "hidden"} p-0 m-0`}
            />
            <video
              ref={playerRefs.two as React.RefObject<HTMLVideoElement>}
              src={videoSources.two}
              width="100%"
              height="100%"
              className={`${selectedVideo === 2 ? "block" : "hidden"}`}
            />
            <video
              ref={playerRefs.three as React.RefObject<HTMLVideoElement>}
              src={videoSources.three}
              width="100%"
              height="100%"
              className={`${selectedVideo === 3 ? "block" : "hidden"}`}
            />
            <video
              ref={playerRefs.four as React.RefObject<HTMLVideoElement>}
              src={videoSources.four}
              width="100%"
              height="100%"
              className={`${selectedVideo === 4 ? "block" : "hidden"}`}
            />
            <video
              ref={playerRefs.five as React.RefObject<HTMLVideoElement>}
              src={videoSources.five}
              width="100%"
              height="100%"
              className={`${selectedVideo === 5 ? "block" : "hidden"}`}
            />
          </div>
        )}
      </div>
    </div>
  );
});

export default PieChartPlayback;