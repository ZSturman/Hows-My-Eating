import React, { useState, useRef, useEffect } from "react";
import { Marker } from "@/types/Markers";
import MarkersLog from "./MarkersLog";
import TimelineSlider from "./Timeline";
import VideoDisplay from "./VideoDisplay";
import ImportedData from "../ImportedData";
import { MovInfo } from "@/types/ChewingData.types";
import { convertFileSrc } from "@tauri-apps/api/core";
import { Button } from "../ui/button";
import { PanelRight } from "lucide-react";

type VideoMarkerProps = {
  movInfo: MovInfo;
  markers: Marker[];
  updateMarkers: (frame: number, newMarker: Marker) => void;
  deleteMarker: (markerId: number) => void;
  clearMarkers: () => void;
};

const VideoMarker: React.FC<VideoMarkerProps> = ({
  movInfo,
  markers,
  updateMarkers,
  deleteMarker,
  clearMarkers,
}) => {
  // State variables
  const [duration, setDuration] = useState<number>(movInfo.duration ?? 0);
  const [fps] = useState<number>(movInfo.fps ?? 30);
  const [totalFrames, setTotalFrames] = useState<number>(
    movInfo.totalFrames ?? 0
  );
  const [currentFrame, setCurrentFrame] = useState<number>(0);
  const [playing, setPlaying] = useState<boolean>(false);

  const [markerId, setMarkerId] = useState<number>(0);
  const [videoSrc] = useState(convertFileSrc(movInfo.videoPath));

  // We use mouthState for both the overlay display and for button highlighting.
  const [mouthState, setMouthState] = useState<{
   mouth: "Open" | "Closed";
    action: "Bite" | "Chew" | "Swallow" | "Other";
  }>({
    mouth: "Closed",
    action: "Other",
  });

  const [showMarkersLog, setShowMarkersLog] = useState<boolean>(true);

  const videoRef = useRef<HTMLVideoElement>(null);

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      if (duration === 0) {
        const vidDuration = videoRef.current.duration;
        setDuration(vidDuration);
      }

      if (totalFrames === 0) {
        setTotalFrames(Math.floor(duration * fps));
      }
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      const time = videoRef.current.currentTime;
      const frame = Math.round(time * fps);
      setCurrentFrame(frame);
    }
  };

  const togglePlayPause = () => {
    if (videoRef.current) {
      if (playing) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setPlaying(!playing);
    }
  };

  const moveToFrame = (frame: number) => {
    if (videoRef.current) {
      const clampedFrame = Math.max(0, Math.min(frame, totalFrames));
      videoRef.current.currentTime = clampedFrame / fps;
      setCurrentFrame(clampedFrame);
    }
  };

  // This function updates mouthState and adds or replaces a marker at the current frame.
  const setMarker = (params: {
    mouth?: "Open" | "Closed";
    action?: "Bite" | "Chew" | "Swallow" | "Other";
  }) => {
    const newMouthState = {
      mouth: params.mouth ?? mouthState.mouth,
      action: params.action ?? mouthState.action,
    };
    // Update state immediately so that the overlay reflects the new values.
    setMouthState(newMouthState);

    if (videoRef.current) {
      const currentTime = videoRef.current.currentTime;
      // Use Math.round here to match handleTimeUpdate.
      const newId = markerId + 1;
      setMarkerId(newId);

      const newMarker: Marker = {
        id: newId,
        frame:currentFrame,
        timestamp: parseFloat(currentTime.toFixed(4)),
        mouth: newMouthState.mouth,
        action: newMouthState.action,
      };

      updateMarkers(currentFrame, newMarker);
    }
  };

  const moveInTimeline = (
    direction: "forward" | "backward",
    amount: "frame" | "jump" | "all"
  ) => {
    if (videoRef.current) {
      const currentFrame = Math.round(videoRef.current.currentTime * fps);
      let newFrame = currentFrame;
      switch (direction) {
        case "forward":
          switch (amount) {
            case "frame":
              newFrame += 1;
              break;
            case "jump":
              newFrame += fps;
              break;
            case "all":
              newFrame = totalFrames;
              break;
          }
          break;
        case "backward":
          switch (amount) {
            case "frame":
              newFrame -= 1;
              break;
            case "jump":
              newFrame -= fps;
              break;
            case "all":
              newFrame = 0;
              break;
          }
          break;
      }
      moveToFrame(newFrame);
    }
  };

  // New functionality: Jump to previous marker
  const jumpToPreviousMarker = () => {
    if (markers.length === 0) moveInTimeline("backward", "all");
    const previousMarkers = markers.filter(
      (marker) => marker.frame < currentFrame
    );
    if (previousMarkers.length === 0) moveInTimeline("backward", "all");
    const closestMarker = previousMarkers.reduce((prev, curr) =>
      curr.frame > prev.frame ? curr : prev
    );
    moveToFrame(closestMarker.frame);
  };

  // New functionality: Jump to next marker
  const jumpToNextMarker = () => {
    if (markers.length === 0) moveInTimeline("forward", "all");
    const nextMarkers = markers.filter((marker) => marker.frame > currentFrame);
    if (nextMarkers.length === 0) moveInTimeline("forward", "all");
    const closestMarker = nextMarkers.reduce((prev, curr) =>
      curr.frame < prev.frame ? curr : prev
    );
    moveToFrame(closestMarker.frame);
  };

  // New functionality: Delete marker at current frame
  const deleteMarkerAtCurrentFrame = () => {
    const markerToDelete = markers.find(
      (marker) => marker.frame === currentFrame
    );
    if (markerToDelete && deleteMarker) {
      deleteMarker(markerToDelete.id);
    }
  };

  // Handle hotkeys.
  const handleKeyDown = (e: KeyboardEvent) => {
    if (
      document.activeElement &&
      (document.activeElement.tagName === "INPUT" ||
        document.activeElement.tagName === "TEXTAREA")
    ) {
      return;
    }

    switch (e.key) {
      case " ":
      case "Spacebar":
        e.preventDefault();
        togglePlayPause();
        break;
      case "ArrowUp":
        moveInTimeline("forward", "jump");
        break;
      case "ArrowDown":
        moveInTimeline("backward", "jump");
        break;
      case "ArrowRight":
        moveInTimeline("forward", "frame");
        break;
      case "ArrowLeft":
        moveInTimeline("backward", "frame");
        break;
      case "1":
        setMarker({ mouth: "Open" });
        break;
      case "2":
        setMarker({ mouth: "Closed" });
        break;
      case "b":
        setMarker({ action: "Bite" });
        break;
      case "c":
        setMarker({ action: "Chew" });
        break;
      case "s":
        setMarker({ action: "Swallow" });
        break;
      case "o":
        setMarker({ action: "Other" });
        break;
      default:
        break;
    }
  };

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [currentFrame, playing, mouthState, markerId, markers]);

  // As the video plays, update mouthState based on the most recent marker at or before the current frame.
  useEffect(() => {
    if (markers.length === 0) return;

    const activeMarker = markers.reduce((prev: Marker | null, curr) => {
      if (curr.frame <= currentFrame) {
        return prev === null || curr.frame > prev.frame ? curr : prev;
      }
      return prev;
    }, null as Marker | null);

    if (activeMarker) {
      setMouthState({
        mouth: activeMarker.mouth,
        action: activeMarker.action,
      });
    }
  }, [currentFrame, markers]);

  const toggleMarkersLogAndImportedData = () => {
    setShowMarkersLog(!showMarkersLog);
  };

  return (
    <div className="h-full">
      <div className="pb-3">

      <TimelineSlider
        totalFrames={totalFrames}
        currentFrame={currentFrame}
        markers={markers}
        moveToFrame={moveToFrame}
        />
        </div>
      <div className="flex flex-row h-full">
        <div className="w-full h-full">
          <VideoDisplay
            videoSrc={videoSrc}
            videoRef={videoRef}
            handleLoadedMetadata={handleLoadedMetadata}
            handleTimeUpdate={handleTimeUpdate}
            currentFrame={currentFrame}
            mouthState={mouthState}
            setMarker={setMarker}
            playing={playing}
            togglePlayPause={togglePlayPause}
            moveInTimeline={moveInTimeline}
            jumpToPreviousMarker={jumpToPreviousMarker}
            jumpToNextMarker={jumpToNextMarker}
            deleteMarkerAtCurrentFrame={deleteMarkerAtCurrentFrame}
            clearMarkers={clearMarkers}
          />
        </div>

        <div className="flex flex-col">
          <Button onClick={toggleMarkersLogAndImportedData}  variant={"outline"}>
            <PanelRight size={24} />
          </Button>
          {showMarkersLog && (
            <div>
              <MarkersLog markers={markers} />
              <ImportedData />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default VideoMarker;
