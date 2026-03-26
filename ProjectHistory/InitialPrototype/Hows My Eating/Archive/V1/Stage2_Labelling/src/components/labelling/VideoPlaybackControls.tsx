import { Button } from "../../components/ui/button"
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Rewind,
  FastForward,
  StepBack,
  StepForward,
  Trash,
  Bookmark,
  ChevronsLeft,
  ChevronsRight,
} from "lucide-react"
import type React from "react" // Added import for React

type VideoPlaybackControlsProps = {
  currentFrame: number
  playing: boolean
  togglePlayPause: () => void
  moveInTimeline: (direction: "backward" | "forward", amount: "frame" | "jump" | "all") => void
  jumpToPreviousMarker: () => void
  jumpToNextMarker: () => void
  deleteMarkerAtCurrentFrame: () => void
  clearMarkers: () => void
}

const VideoPlaybackControls: React.FC<VideoPlaybackControlsProps> = ({
  currentFrame,
  playing,
  togglePlayPause,
  moveInTimeline,
  jumpToPreviousMarker,
  jumpToNextMarker,
  deleteMarkerAtCurrentFrame,
  clearMarkers,
}) => {
  return (
    <div className="flex flex-col items-center bg-zinc-200/90 rounded-md p-4 relative">
      <div className="absolute top-2 left-2 text-black text-sm font-medium">Frame: {currentFrame}</div>


      <div className="flex items-center justify-center space-x-2">
        <Button
          onClick={() => moveInTimeline("backward", "all")}
          className="bg-transparent text-black hover:bg-zinc-300"
          aria-label="Go to start"
        >
          <ChevronsLeft className="h-5 w-5" />
        </Button>
        <Button
          onClick={() => moveInTimeline("backward", "jump")}
          className="bg-transparent text-black hover:bg-zinc-300"
          aria-label="Rewind"
        >
          <Rewind className="h-5 w-5" />
        </Button>
        <Button
          onClick={() => moveInTimeline("backward", "frame")}
          className="bg-transparent text-black hover:bg-zinc-300"
          aria-label="Previous frame"
        >
          <StepBack className="h-5 w-5" />
        </Button>
        <Button
          onClick={togglePlayPause}
               className="bg-transparent text-black hover:bg-zinc-300"
          aria-label={playing ? "Pause" : "Play"}
        >
          {playing ? <Pause className="h-8 w-8" /> : <Play className="h-8 w-8" />}
        </Button>


        <Button
          onClick={() => moveInTimeline("forward", "frame")}
          className="bg-transparent text-black hover:bg-zinc-300"
          aria-label="Next frame"
        >
          <StepForward className="h-5 w-5" />
        </Button>
        <Button
          onClick={() => moveInTimeline("forward", "jump")}
          className="bg-transparent text-black hover:bg-zinc-300"
          aria-label="Fast forward"
        >
          <FastForward className="h-5 w-5" />
        </Button>
        <Button
          onClick={() => moveInTimeline("forward", "all")}
          className="bg-transparent text-black hover:bg-zinc-300"
          aria-label="Go to end"
        >
          <ChevronsRight className="h-5 w-5" />
        </Button>
      </div>

      <div className="flex items-center justify-center mt-4 space-x-2">
        <Button
          onClick={jumpToPreviousMarker}
          className="bg-transparent text-black hover:bg-zinc-300"
          aria-label="Previous marker"
        >
          <SkipBack className="h-5 w-5" />
        </Button>
        <Button
          onClick={deleteMarkerAtCurrentFrame}
          className="bg-transparent text-black hover:bg-zinc-300"
          aria-label="Delete current marker"
        >
          <Trash className="h-5 w-5" />
        </Button>
        <Button
          onClick={clearMarkers}
          className="bg-transparent text-black hover:bg-zinc-300"
          aria-label="Clear all markers"
        >
          <Bookmark className="h-5 w-5" />
        </Button>
        <Button
          onClick={jumpToNextMarker}
          className="bg-transparent text-black hover:bg-zinc-300"
          aria-label="Next marker"
        >
          <SkipForward className="h-5 w-5" />
        </Button>
      </div>
    </div>
  )
}

export default VideoPlaybackControls

