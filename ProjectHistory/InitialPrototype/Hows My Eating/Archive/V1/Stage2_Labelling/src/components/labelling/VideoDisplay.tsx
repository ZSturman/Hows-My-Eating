import React, { useRef, useState } from "react";
import ControlPanel from "./ControlPanel";
import { Button } from "../ui/button";
import { ArrowDown, ArrowUp } from "lucide-react";

interface VideoDisplayProps {
  videoSrc: string;
  videoRef: React.RefObject<HTMLVideoElement>;
  handleLoadedMetadata: () => void;
  handleTimeUpdate: () => void;
  currentFrame: number;
  // Use the current mouth state for both the overlay and the controls.
  mouthState: {
    mouth: "Open" | "Closed";
    action: "Bite" | "Chew" | "Swallow" | "Other";
  };
  setMarker: (params: {
    mouth?: "Open" | "Closed";
    action?: "Bite" | "Chew" | "Swallow" | "Other";
  }) => void;
  playing: boolean;
  togglePlayPause: () => void;
  moveInTimeline: (
    direction: "backward" | "forward",
    amount: "frame" | "jump" | "all"
  ) => void;
  jumpToPreviousMarker: () => void;
  jumpToNextMarker: () => void;
  deleteMarkerAtCurrentFrame: () => void;
  clearMarkers: () => void;
}

const VideoDisplay: React.FC<VideoDisplayProps> = ({
  videoSrc,
  videoRef,
  handleLoadedMetadata,
  handleTimeUpdate,
  currentFrame,
  mouthState,
  setMarker,
  playing,
  togglePlayPause,
  moveInTimeline,
  jumpToPreviousMarker,
  jumpToNextMarker,
  deleteMarkerAtCurrentFrame,
  clearMarkers,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  // zoomLevel: 1 means no zoom, 1.5 is the first zoom state, and 2 is the second zoom state.
  const [zoomLevel, setZoomLevel] = useState<number>(1);
  // panY is the vertical offset in pixels.
  const [panY, setPanY] = useState<number>(0);

  // Cycle between the three zoom levels.
  const cycleZoomLevel = () => {
    if (zoomLevel === 1) {
      setZoomLevel(1.5);
    } else if (zoomLevel === 1.5) {
      setZoomLevel(2);
    } else {
      setZoomLevel(1);
      setPanY(0); // Optionally reset pan when returning to normal.
    }
  };

  // Adjust the vertical pan offset.
  const panUp = () => {
    setPanY((prev) => prev + 40);
  };

  const panDown = () => {
    // Adding moves the video downward (revealing its bottom).
    setPanY((prev) => prev - 40);
  };

  return (
    <div
      ref={containerRef}
      className="relative flex justify-center items-center max-w-[90vw] max-h-[85vh] overflow-hidden bg-zinc-900"
    >
      <video
        ref={videoRef}
        src={videoSrc}
        onLoadedMetadata={handleLoadedMetadata}
        onTimeUpdate={handleTimeUpdate}
        className="object-contain max-w-[90vw] max-h-[100vh]"
        style={{
          backgroundColor: "black",
          // Applying translation first and then scaling ensures that the pan offset (in pixels)
          // is not multiplied by the zoom level.
          transform: `translateY(${panY}px) scale(${zoomLevel})`,
          transformOrigin: "center center",
          transition: "transform 0.3s ease",
        }}
      />
      {/* Overlay for marker control buttons */}
      <ControlPanel
        playing={playing}
        togglePlayPause={togglePlayPause}
        moveInTimeline={moveInTimeline}
        currentFrame={currentFrame}
        mouthState={mouthState}
        setMarker={setMarker}
        jumpToPreviousMarker={jumpToPreviousMarker}
        jumpToNextMarker={jumpToNextMarker}
        deleteMarkerAtCurrentFrame={deleteMarkerAtCurrentFrame}
        clearMarkers={clearMarkers}
      />
      <div className="absolute top-2 right-2 flex flex-col gap-1">
        <Button onClick={cycleZoomLevel} variant="outline">
          {zoomLevel === 1 ? "(1x)" : zoomLevel === 1.5 ? "(1.5x)" : "(2x)"}
        </Button>
        {zoomLevel !== 1 && (
          <div className="flex flex-col gap-1">
            <Button onClick={panUp} variant="outline">
              <ArrowUp />
            </Button>
            <Button onClick={panDown} variant="outline">
              <ArrowDown />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default VideoDisplay;
