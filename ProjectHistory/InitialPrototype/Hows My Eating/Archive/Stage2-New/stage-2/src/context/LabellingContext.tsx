import React, {
  createContext,
  useReducer,
  useContext,
  useEffect,
  useRef,
  useCallback,
  useState,
} from "react";
import ReactPlayer from "react-player";
import { appDataDir, join } from "@tauri-apps/api/path";
import { convertFileSrc } from "@tauri-apps/api/tauri";
import { useKeyboard } from "./KeyboardContext";
import { PiCommand } from "react-icons/pi";
import {
  FaArrowDown,
  FaArrowLeft,
  FaArrowRight,
  FaArrowUp,
} from "react-icons/fa";
import { MdOutlineKeyboardOptionKey } from "react-icons/md";

type LabelState = {
  movPath: string;
  isPlaying: boolean;
  currentFrameIndex: number;
  totalFrames: number;
  playbackRate: number;
  lastSetLabels: Labels;
  labelHistory: Map<number, Labels>;
};

type LabelAction =
  | { type: "INSTANTIATE_LABELS"; labels: Labels[] }
  | { type: "INSTANTIATE_MOV"; selectedData: DataRecord; movPath: string }
  | { type: "ADD_LABEL"; label: Labels }
  | { type: "REMOVE_LABEL"; frameIndex: number }
  | { type: "PLAY_PAUSE" }
  | { type: "FRAME_FORWARD" }
  | { type: "FRAME_BACKWARD" }
  | { type: "SKIP_FORWARD" }
  | { type: "SKIP_BACKWARD" }
  | { type: "CHANGE_SPEED" }
  | { type: "UPDATE_FRAME_INDEX"; frameIndex: number }
  | { type: "ERROR_LOADING_LABELS" }
  | { type: "ERROR_LOADING_MOV" };

const initialLabelState: LabelState = {
  movPath: "",
  isPlaying: false,
  currentFrameIndex: 0,
  totalFrames: 0,
  playbackRate: 1, // Default speed is normal (1x)
  lastSetLabels: {
    isEating: false,
    isTalking: false,
    mouthState: "CLOSED",
    primaryBodyState: "SITTING",
    mouthAction: "",
    bodyAction: "",
    otherLabels: [],
    frameIndex: 0,
  },
  labelHistory: new Map<number, Labels>(),
};

const LabelContext = createContext<{
  state: LabelState;
  dispatch: React.Dispatch<LabelAction>;
}>({
  state: initialLabelState,
  dispatch: () => null,
});

const LabelReducer = (state: LabelState, action: LabelAction): LabelState => {
  switch (action.type) {
    case "INSTANTIATE_LABELS":
      const labelMap = new Map<number, Labels>(
        action.labels.map((label) => [label.frameIndex, label])
      );
      return {
        ...state,
        labelHistory: labelMap,
      };
    case "INSTANTIATE_MOV":
      return {
        ...state,
        movPath: action.movPath,
        totalFrames: action.selectedData.movData.totalFrames,
      };
    case "ADD_LABEL":
      const newLabelHistory = new Map(state.labelHistory);
      const existingLabel = newLabelHistory.get(state.currentFrameIndex);

      // Check if the new label is different from the existing one
      if (JSON.stringify(existingLabel) !== JSON.stringify(action.label)) {
        const updatedLabel = {
          ...(existingLabel || {}),
          ...action.label,
          frameIndex: state.currentFrameIndex,
        };
        newLabelHistory.set(state.currentFrameIndex, updatedLabel);

        return {
          ...state,
          lastSetLabels: updatedLabel,
          labelHistory: newLabelHistory,
        };
      }
      return state; // Return unchanged state if no difference

    case "REMOVE_LABEL":
      const updatedLabelHistory = new Map(state.labelHistory);
      updatedLabelHistory.delete(action.frameIndex);
      return {
        ...state,
        labelHistory: updatedLabelHistory,
      };

    case "UPDATE_FRAME_INDEX":
      const newFrameIndex = action.frameIndex;
      const labelsAtNewFrame = state.labelHistory.get(newFrameIndex);

      return {
        ...state,
        currentFrameIndex: newFrameIndex,
        lastSetLabels: labelsAtNewFrame || state.lastSetLabels,
      };
    case "CHANGE_SPEED":
      const playbackSpeeds = [1, 0.5, 0.25, 1.5, 2];
      const currentSpeedIndex = playbackSpeeds.indexOf(state.playbackRate);
      const newSpeedIndex = (currentSpeedIndex + 1) % playbackSpeeds.length;
      const newSpeed = playbackSpeeds[newSpeedIndex];
      return {
        ...state,
        playbackRate: newSpeed,
      };

    case "PLAY_PAUSE":
      return {
        ...state,
        isPlaying: !state.isPlaying,
      };
    case "FRAME_FORWARD":
      const forwardTimestamp = Math.min(
        state.currentFrameIndex + 1,
        state.totalFrames
      );
      const forwardLabel = state.labelHistory.get(forwardTimestamp);

      return {
        ...state,
        currentFrameIndex: forwardTimestamp,
        lastSetLabels: forwardLabel || state.lastSetLabels,
      };
    case "FRAME_BACKWARD":
      const backwardTimestamp = Math.max(state.currentFrameIndex - 1, 0);
      const backwardLabel = state.labelHistory.get(backwardTimestamp);

      return {
        ...state,
        currentFrameIndex: backwardTimestamp,
        lastSetLabels: backwardLabel || state.lastSetLabels,
      };
    case "SKIP_FORWARD":
      const skipForwardTimestamp = Math.min(
        state.currentFrameIndex + 120,
        state.totalFrames
      );
      const skipForwardLabel = state.labelHistory.get(skipForwardTimestamp);

      return {
        ...state,
        currentFrameIndex: skipForwardTimestamp,
        lastSetLabels: skipForwardLabel || state.lastSetLabels,
      };
    case "SKIP_BACKWARD":
      const skipBackwardTimestamp = Math.max(state.currentFrameIndex - 240, 0);
      const skipBackwardLabel = state.labelHistory.get(skipBackwardTimestamp);

      return {
        ...state,
        currentFrameIndex: skipBackwardTimestamp,
        lastSetLabels: skipBackwardLabel || state.lastSetLabels,
      };
    case "ERROR_LOADING_LABELS":
      return {
        ...state,
        labelHistory: new Map<number, Labels>(),
      };
    case "ERROR_LOADING_MOV":
      return {
        ...state,
        movPath: "",
      };
    default:
      return state;
  }
};

export const LabelProvider: React.FC<{
  children: React.ReactNode;
  selectedData: DataRecord;
}> = ({ children, selectedData }) => {
  const [state, dispatch] = useReducer(LabelReducer, initialLabelState);
  const { pressedKeys } = useKeyboard();
  const playerRef = useRef<ReactPlayer>(null);
  const [changeCurrentTimestamp, setChangeCurrentTimestamp] =
    useState<boolean>(false);

  useEffect(() => {
    const controller = new AbortController();
    const { signal } = controller;

    const getCorrectSource = async () => {
      try {
        const source = await appDataDir();
       const correctPath = await join(source, selectedData.movData.path);
        //const correctPath = "/Users/zacharysturman/Desktop/Stage2-New/stage-2/public/mouth_points.webm"
        if (!signal.aborted) {
          const tauriPath = convertFileSrc(correctPath);
          dispatch({
            type: "INSTANTIATE_MOV",
            selectedData: selectedData,
            movPath: tauriPath,
          });
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
  }, [selectedData]);

  useEffect(() => {
    if (changeCurrentTimestamp) {
      if (playerRef.current) {
        playerRef.current.seekTo(
          state.currentFrameIndex / selectedData.movData.fps,
          "seconds"
        );
      }
      setChangeCurrentTimestamp(false);
    }
  }, [changeCurrentTimestamp]);

  useEffect(() => {
    if (selectedData.labelledData) {
      dispatch({
        type: "INSTANTIATE_LABELS",
        labels: selectedData.labelledData.labels,
      });
    } else {
      dispatch({ type: "ERROR_LOADING_LABELS" });
    }
  }, [selectedData]);

  useEffect(() => {
    if (state.isPlaying) {
      playerRef.current?.getInternalPlayer().play();
    } else {
      playerRef.current?.getInternalPlayer().pause();
    }
  }, [state.isPlaying]);

  // useEffect(() => {
  //   if (playerRef.current) {
  //     const fps = selectedData.movData.fps;
  //     const currentTime = state.currentFrameIndex / fps;
  //     playerRef.current.seekTo(currentTime, "seconds");
  //   }
  // }, [state.currentFrameIndex, selectedData.movData.fps]);

  useEffect(() => {
    if (pressedKeys.size > 0) {
      if (pressedKeys.size === 1) {
        if (
          pressedKeys.has("arrowup") ||
          pressedKeys.has("arrowdown") ||
          pressedKeys.has("arrowleft") ||
          pressedKeys.has("arrowright") ||
          pressedKeys.has("t") ||
          pressedKeys.has("e") ||
          pressedKeys.has("d") ||
          pressedKeys.has("l") ||
          pressedKeys.has("y") ||
          pressedKeys.has("b") ||
          pressedKeys.has("q")
        ) {
          let currentLabels = state.lastSetLabels;
          if (pressedKeys.has("arrowup")) {
            currentLabels.mouthState = "OPEN";
          } else if (pressedKeys.has("arrowdown")) {
            currentLabels.mouthState = "CLOSED";
          } else if (pressedKeys.has("arrowleft")) {
            currentLabels.mouthState = "OPENING";
          } else if (pressedKeys.has("arrowright")) {
            currentLabels.mouthState = "CLOSING";
          } else if (pressedKeys.has("t")) {
            currentLabels.isTalking = !currentLabels.isTalking;
          } else if (pressedKeys.has("e")) {
            currentLabels.isEating = !currentLabels.isEating;
          } else if (pressedKeys.has("d")) {
            currentLabels.mouthAction = "DRINKING";
          } else if (pressedKeys.has("l")) {
            currentLabels.mouthAction = "LAUGHING";
          } else if (pressedKeys.has("y")) {
            currentLabels.mouthAction = "YAWNING";
          } else if (pressedKeys.has("b")) {
            currentLabels.mouthAction = "BITING";
          } else if (pressedKeys.has("q")) {
            currentLabels.mouthAction = "";
          }
          dispatch({ type: "ADD_LABEL", label: currentLabels });
        } else if (pressedKeys.has(" ")) {
          dispatch({ type: "PLAY_PAUSE" });
        } else if (pressedKeys.has("enter")) {
          dispatch({ type: "CHANGE_SPEED" });
        }
      } else if (pressedKeys.size === 2) {
        if (pressedKeys.has("alt")) {
          let currentLabels = state.lastSetLabels;
          if (pressedKeys.has("arrowleft")) {
            currentLabels.bodyAction = "LEAN_LEFT";
          } else if (pressedKeys.has("arrowright")) {
            currentLabels.bodyAction = "LEAN_RIGHT";
          } else if (pressedKeys.has("arrowup")) {
            currentLabels.bodyAction = "LEAN_FORWARD";
          } else if (pressedKeys.has("arrowdown")) {
            currentLabels.bodyAction = "LEAN_BACKWARD";
          }
          dispatch({ type: "ADD_LABEL", label: currentLabels });
        } else if (pressedKeys.has("arrowright") && pressedKeys.has("meta")) {
          dispatch({
            type: "FRAME_FORWARD",
          });
          setChangeCurrentTimestamp(true);
        } else if (pressedKeys.has("arrowleft") && pressedKeys.has("meta")) {
          dispatch({
            type: "FRAME_BACKWARD",
          });
          setChangeCurrentTimestamp(true);
        } else if (pressedKeys.has("arrowright") && pressedKeys.has("shift")) {
          dispatch({
            type: "SKIP_FORWARD",
          });
          setChangeCurrentTimestamp(true);
        } else if (pressedKeys.has("arrowleft") && pressedKeys.has("shift")) {
          dispatch({
            type: "SKIP_BACKWARD",
          });
          setChangeCurrentTimestamp(true);
        }
      }
    }
  }, [pressedKeys]);

  // Define a generic type for the callback function
  type CallbackFunction = (...args: any[]) => void;

  const useDebounce = (callback: CallbackFunction, delay: number) => {
    const timerRef = useRef<NodeJS.Timeout | null>(null);

    const debouncedFunction = useCallback(
      (...args: any[]) => {
        if (timerRef.current) {
          clearTimeout(timerRef.current);
        }
        timerRef.current = setTimeout(() => {
          callback(...args);
        }, delay);
      },
      [callback, delay]
    );

    return debouncedFunction;
  };
  const handleProgress = useDebounce(
    (progress: { playedSeconds: number }) => {
      // Calculate the frame index based on the timestamp and fps
      const fps = selectedData.movData.fps;
      const frameIndex = Math.floor(progress.playedSeconds * fps); // Convert seconds to frames

      dispatch({ type: "UPDATE_FRAME_INDEX", frameIndex: frameIndex });
    },
    100 // 100ms delay for debouncing
  );

  return (
    <LabelContext.Provider value={{ state, dispatch }}>
      {state.movPath && (
        <div>
          <div className="w-full text-center">
            {state.labelHistory.size > 0 && (
              <div>
                {Array.from(state.labelHistory.entries()).map(
                  ([frameIndex, labels]) => (
                    <div key={frameIndex}>
                      <p>{labels.frameIndex}</p>
                      <p>{JSON.stringify(labels)}</p>

                      <button
                        onClick={() =>
                          dispatch({ type: "REMOVE_LABEL", frameIndex })
                        }
                      >
                        Remove
                      </button>
                    </div>
                  )
                )}
              </div>
            )}
          </div>

          <div className="flex flex-row  w-full items-center justify-center">
            <div className="relative">
              <div className="absoluter top-0 left-0">{state.playbackRate}</div>

              <ReactPlayer
                ref={playerRef}
                url={state.movPath}
                playing={state.isPlaying}
                playbackRate={state.playbackRate}
                width={
                  selectedData.movData.width > 500
                    ? 500
                    : selectedData.movData.width
                }
                height={
                  selectedData.movData.height > 720
                    ? 720
                    : selectedData.movData.height
                }
                onProgress={handleProgress}
                controls
              />
            </div>
            <div className=" h-full ">
              <div className="flex flex-col w-full p-6 space-y-6 bg-white rounded-md shadow-lg ml-4 border border-gray-200">
                <div className="mb-4">
                  <h2 className="text-xl font-semibold mb-2">Current Labels</h2>
                  <div className="text-sm text-gray-700 space-y-2">
                    <p>
                      <span className="font-medium">Eating State:</span>{" "}
                      {state.lastSetLabels.isEating ? "Eating" : "Not Eating"}
                    </p>
                    <p>
                      <span className="font-medium">Talking State:</span>{" "}
                      {state.lastSetLabels.isTalking
                        ? "Talking"
                        : "Not Talking"}
                    </p>
                    <p>
                      <span className="font-medium">Mouth State:</span>{" "}
                      {state.lastSetLabels.mouthState}
                    </p>
                    <p>
                      <span className="font-medium">Primary Body State:</span>{" "}
                      {state.lastSetLabels.primaryBodyState}
                    </p>
                    <p>
                      <span className="font-medium">Mouth Action:</span>{" "}
                      {state.lastSetLabels.mouthAction || "None"}
                    </p>
                    <p>
                      <span className="font-medium">Body Action:</span>{" "}
                      {state.lastSetLabels.bodyAction || "None"}
                    </p>
                    {state.lastSetLabels.otherLabels.length > 0 && (
                      <p>
                        <span className="font-medium">Other Labels:</span>{" "}
                        {state.lastSetLabels.otherLabels.join(", ")}
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex flex-row">
                  <div className="flex flex-col items-end justify-between">
                    <div className="border-2 border-solid border-black rounded-md p-1 flex flex-row items-center justify-center gap-2">
                      <PiCommand />
                      Home
                    </div>

                    <div
                      className={`border-2 border-solid border-black rounded-md p-1 flex flex-row items-center justify-center gap-2 ${
                        state.lastSetLabels.mouthState === "OPENING"
                          ? "bg-green-500"
                          : "bg-red-500"
                      }`}
                      onClick={() =>
                        dispatch({
                          type: "ADD_LABEL",
                          label: {
                            ...state.lastSetLabels,
                            mouthState: "OPENING",
                          },
                        })
                      }
                    >
                      <FaArrowLeft />
                      <div>Opening</div>
                    </div>
                  </div>

                  <div className="flex flex-col justify-between gap-2 items-center mx-1">
                    <div
                      className={`border-2 border-solid border-black rounded-md p-1 flex flex-row items-center justify-center gap-2 ${
                        state.lastSetLabels.mouthState === "OPEN"
                          ? "bg-green-500"
                          : "bg-red-500"
                      }`}
                      onClick={() =>
                        dispatch({
                          type: "ADD_LABEL",
                          label: { ...state.lastSetLabels, mouthState: "OPEN" },
                        })
                      }
                    >
                      <FaArrowUp />
                      <div>Open</div>
                    </div>

                    <div
                      className={`border-2 border-solid border-black rounded-md p-1 flex flex-row items-center justify-center gap-2 ${
                        state.lastSetLabels.mouthState === "CLOSED"
                          ? "bg-green-500"
                          : "bg-red-500"
                      }`}
                      onClick={() =>
                        dispatch({
                          type: "ADD_LABEL",
                          label: {
                            ...state.lastSetLabels,
                            mouthState: "CLOSED",
                          },
                        })
                      }
                    >
                      <FaArrowDown />
                      <div>Closed</div>
                    </div>
                  </div>

                  <div className="flex flex-col justify-between items-start">
                    <div className="border-2 border-solid border-black rounded-md p-1 flex flex-row items-center justify-center gap-2">
                      <MdOutlineKeyboardOptionKey />
                      Back
                    </div>
                    <div
                      className={`border-2 border-solid border-black rounded-md p-1 flex flex-row items-center justify-center gap-2 ${
                        state.lastSetLabels.mouthState === "CLOSING"
                          ? "bg-green-500"
                          : "bg-red-500"
                      }`}
                      onClick={() =>
                        dispatch({
                          type: "ADD_LABEL",
                          label: {
                            ...state.lastSetLabels,
                            mouthState: "CLOSING",
                          },
                        })
                      }
                    >
                      <FaArrowRight />
                      <div>Closing</div>
                    </div>
                  </div>
                </div>

                <div className="mt-4">
                  <div className="flex flex-wrap gap-2">
                    <button
                      className="px-3 py-1 text-sm font-medium text-white bg-blue-500 rounded hover:bg-blue-600"
                      onClick={() =>
                        dispatch({
                          type: "ADD_LABEL",
                          label: {
                            ...state.lastSetLabels,
                            isEating: !state.lastSetLabels.isEating,
                          },
                        })
                      }
                    >
                      Toggle Eating State
                    </button>
                    <button
                      className="px-3 py-1 text-sm font-medium text-white bg-blue-500 rounded hover:bg-blue-600"
                      onClick={() =>
                        dispatch({
                          type: "ADD_LABEL",
                          label: {
                            ...state.lastSetLabels,
                            isTalking: !state.lastSetLabels.isTalking,
                          },
                        })
                      }
                    >
                      Toggle Talking State
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
      {children}
    </LabelContext.Provider>
  );
};

export const useLabelContext = () => useContext(LabelContext);
