import { useState, useRef, useCallback, useEffect } from "react"
import useEmblaCarousel from "embla-carousel-react"
import { Button } from "../../components/ui/button"
import { Check, X, Undo2, ChevronLeft, ChevronRight, Loader2, CircleCheck } from "lucide-react"
import type { VideoChunkStatus } from "@/types/Markers"
import { convertFileSrc } from "@tauri-apps/api/core"

interface VideoCarouselProps {
  videos: VideoChunkStatus[]
  handleUndo: (index: number) => void
  handleVerify: (index: number, value: boolean) => void
}

export function VideoCarousel({ videos, handleUndo, handleVerify }: VideoCarouselProps) {
  const [emblaRef, emblaApi] = useEmblaCarousel({ loop: true })
  const [currentIndex, setCurrentIndex] = useState(0)
  const videoRefs = useRef<(HTMLVideoElement | null)[]>([])
  const [visibleRange, setVisibleRange] = useState({ start: 0, end: 2 })
  const [loadingVideos, setLoadingVideos] = useState<Record<number, boolean>>({})

  const scrollPrev = useCallback(() => emblaApi?.scrollPrev(), [emblaApi])
  const scrollNext = useCallback(() => emblaApi?.scrollNext(), [emblaApi])

  const onSelect = useCallback(() => {
    if (!emblaApi) return
    const index = emblaApi.selectedScrollSnap()
    setCurrentIndex(index)
    setVisibleRange({
      start: Math.max(0, index - 1),
      end: Math.min(videos.length - 1, index + 1),
    })
  }, [emblaApi, videos.length])

  useEffect(() => {
    if (!emblaApi) return;
    onSelect();
    emblaApi.on("select", onSelect);
    return () => {
      emblaApi.off("select", onSelect);
    };
  }, [emblaApi, onSelect]);

  useEffect(() => {
    const currentVideo = videoRefs.current[currentIndex]
    if (currentVideo) {
      currentVideo.play().catch((error) => console.error("Error playing video:", error))
    }
    return () => {
      if (currentVideo) {
        currentVideo.pause()
      }
    }
  }, [currentIndex])

  const handleVideoIsVerified = (index: number, correct: boolean) => {
    handleVerify(index, correct)
    scrollNext()
  }

  const handleVideoLoad = (index: number) => {
    setLoadingVideos((prev) => {
      const newLoading = { ...prev }
      delete newLoading[index]
      return newLoading
    })
  }

  const handleVideoStartLoading = (index: number) => {
    setLoadingVideos((prev) => ({ ...prev, [index]: true }))
  }


  return (
    <div className="relative max-w-3xl mx-auto  h-[70vh]">
      <div className="overflow-x-hidden overflow-y-scroll" ref={emblaRef}>
        <div className="flex">
          {videos.map((video, index) => (
            <div key={index} className="flex-[0_0_100%] min-w-0 relative">
              {index >= visibleRange.start && index <= visibleRange.end && (
                <div className="relative rounded-lg py-5">
                  {loadingVideos[index] && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50 rounded-lg">
                      <Loader2 className="w-8 h-8 text-white animate-spin" />
                    </div>
                  )}
                  <video
                    ref={(el) => (videoRefs.current[index] = el)}
                    src={convertFileSrc(video.filePath)}
                    className="object-contain  mx-auto rounded-lg h-[50vh]"
                    style={{ backgroundColor: "black" }}
                    preload="metadata"
                    onLoadStart={() => handleVideoStartLoading(index)}
                    onLoadedData={() => handleVideoLoad(index)}
                    controls
                  />
                </div>
              )}

              <div className="w-full text-center font-bold text-3xl mt-4 mb-6">{index+1} {" "}Is this a {video.originalValue}?</div>

              {!loadingVideos[index] && video.verified ?
              
              
              
              (
                <div className="absolute inset-0 bg-black bg-opacity-75 flex flex-col items-center justify-center rounded-lg">
                  <span className="text-white text-6xl  flex items-center my-20">
                    <CircleCheck className="mr-2 h-16 w-16" /> Verified
                  </span>
                  <Button onClick={() => handleUndo(index)} variant="outline" className="text-lg py-3 px-6">
                    <Undo2 className="mr-2 h-5 w-5" /> Undo
                  </Button>
                </div>
              ) :  (
                <div className="flex justify-center space-x-4 mt-4">
                  <Button onClick={() => handleVideoIsVerified(index, true)} variant="default" className="text-lg py-3 px-6">
                    <Check className="mr-2 h-5 w-5" /> Yes
                  </Button>
                  <Button onClick={() => handleVideoIsVerified(index, false)} variant="destructive" className="text-lg py-3 px-6">
                    <X className="mr-2 h-5 w-5" /> No
                  </Button>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
      <Button
        onClick={scrollPrev}
        className="absolute left-4 top-1/2 transform -translate-y-1/2"
        variant="outline"
        size="icon"
      >
        <ChevronLeft className="h-6 w-6" />
      </Button>
      <Button
        onClick={scrollNext}
        className="absolute right-4 top-1/2 transform -translate-y-1/2"
        variant="outline"
        size="icon"
      >
        <ChevronRight className="h-6 w-6" />
      </Button>
    </div>
  )
}

