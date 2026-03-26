import MarkerControlsOverlay from "./MarkerControlsOverlay";
import VideoPlaybackControls from "./VideoPlaybackControls";

// ControlPanel renders the play/pause and save markers buttons.
interface ControlPanelProps {
  playing: boolean;
  togglePlayPause: () => void;
  moveInTimeline: (
    direction: "backward" | "forward",
    amount: "frame" | "jump" | "all"
  ) => void;
  currentFrame: number;
  mouthState: { mouth: "Open" | "Closed", action: "Bite" | "Chew" | "Swallow" | "Other"};
  setMarker: (params: {
    mouth?: "Open" | "Closed";
    action?: "Bite" | "Chew" | "Swallow" | "Other";
  }) => void;
  jumpToPreviousMarker: () => void;
  jumpToNextMarker: () => void;
  deleteMarkerAtCurrentFrame: () => void;
  clearMarkers: () => void;
}

const ControlPanel: React.FC<ControlPanelProps> = ({
  playing,
  togglePlayPause,
  moveInTimeline,
  currentFrame,
  mouthState,
  setMarker,
  jumpToPreviousMarker,
  jumpToNextMarker,
  deleteMarkerAtCurrentFrame,
  clearMarkers,
}) => {
  return (
    <div className="absolute bottom-0 left-0 w-full p-1">
      <MarkerControlsOverlay mouthState={mouthState} setMarker={setMarker} />
      <VideoPlaybackControls
        currentFrame={currentFrame}
        playing={playing}
        togglePlayPause={togglePlayPause}
        moveInTimeline={moveInTimeline}
        jumpToPreviousMarker={jumpToPreviousMarker}
        jumpToNextMarker={jumpToNextMarker}
        deleteMarkerAtCurrentFrame={deleteMarkerAtCurrentFrame}
        clearMarkers={clearMarkers}
      />
    </div>
  );
};

export default ControlPanel;
