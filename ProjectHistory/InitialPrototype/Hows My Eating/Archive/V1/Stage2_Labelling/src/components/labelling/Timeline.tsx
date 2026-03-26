import type { Marker } from "../../types/Markers"
import { useRef, useState, useEffect } from "react"
import { Slider } from "../../components/ui/slider"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "../../components/ui/tooltip"
import { ArrowBigDown } from "lucide-react"

interface TimelineSliderProps {
  totalFrames: number
  currentFrame: number
  markers: Marker[]
  moveToFrame: (frame: number) => void
}

const TimelineSlider: React.FC<TimelineSliderProps> = ({ totalFrames, currentFrame, markers, moveToFrame }) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const [containerWidth, setContainerWidth] = useState<number>(0)

  useEffect(() => {
    if (!containerRef.current) return

    console.log("containerWidth", containerWidth)

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setContainerWidth(entry.contentRect.width)
      }
    })

    resizeObserver.observe(containerRef.current)

    return () => {
      resizeObserver.disconnect()
    }
  }, [])

  return (
    <div ref={containerRef} className="relative w-full mt-8 mb-4">
      <div className="absolute -top-6 left-0 w-full h-6">
        <TooltipProvider>
          {markers.map((marker, index) => {
            const left = (marker.frame / totalFrames) * 100
            return (
              <Tooltip key={index}>
                <TooltipTrigger asChild>
                  <div
                    className="absolute bottom-0 transform -translate-x-1/2 cursor-pointer"
                    style={{ left: `${left}%` }}
                  >
                    <ArrowBigDown className="w-4 h-4 " />
                  </div>
                </TooltipTrigger>
                <TooltipContent side="top" className="bg-zinc-800 text-white p-2 rounded shadow-lg">
                  <p className="font-semibold">Frame: {marker.frame}</p>
                  <p>Mouth: {marker.mouth}</p>
                  <p>Action: {marker.action}</p>
                </TooltipContent>
              </Tooltip>
            )
          })}
        </TooltipProvider>
      </div>
      <Slider
        min={0}
        max={totalFrames}
        value={[currentFrame]}
        onValueChange={(value) => moveToFrame(value[0])}
        className="w-full"
      />
      <div className="absolute -bottom-6 left-0 text-sm text-gray-500">
        Frame: {currentFrame} / {totalFrames}
      </div>
    </div>
  )
}

export default TimelineSlider

