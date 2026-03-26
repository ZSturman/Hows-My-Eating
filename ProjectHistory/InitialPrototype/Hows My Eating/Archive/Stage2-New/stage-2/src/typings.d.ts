type DataRecord = ValidatedDataForDataRecord & {
  id: number; // Unique identifier for the data record
  dateAdded: number; // Timestamp of when the data was added
  lastModified: number; // Timestamp of when the data was last modified
  dataDirectory: string; // Directory where the data is stored
  originalDataPath: string; // Path to the original data directory
  exortPath: string; // Path to the export directory
  exportStatus: boolean; // Flag indicating if the data has been exported
  isLabelingComplete: boolean; // Flag indicating if all frames have been labeled
  isDataSynced: boolean; // Flag indicating if data is synchronized
  syncOffset: number; // Offset for synchronizing data. This can be used to align motion data with video data¸
};

type ValidatedDataForDataRecord = {
  movData: {
    path: string;
    duration: number;
    width: number;
    height: number;
    fps: number;
    totalFrames: number;
  };
  motionData: {
    path: string;
    duration: number;
    totalEntries: number;
  };
  audioData: {
    path: string;
    duration: number;
    channels: number;
    sampleRate: number;
  };
  csvData: {
    path: string;
    totalRows: number;
  };
  labelledData: {
    path: string;
    labels: Labels[];
  };
};

type MouthState = "OPEN" | "CLOSED" | "OPENING" | "CLOSING";

type PrimaryBodyState =
  | "SITTING"
  | "STANDING"
  | "WALKING"
  | "LYING_DOWN"
  | "OTHER";

type BodyAction =
  | "LEAN_FORWARD"
  | "LEAN_BACKWARD"
  | "LEAN_LEFT"
  | "LEAN_RIGHT"
  | "";

type MouthAction =
  | "DRINKING"
  | "LAUGHING"
  | "YAWNING"
  | "BITING"
  | "CHEWING"
  | "";

type Labels = {
  isEating: boolean;
  isTalking: boolean;
  mouthState: MouthState; // State of the mouth
  mouthAction: MouthAction; // Action associated with the mouth state
  primaryBodyState: PrimaryBodyState; // The action associated with the whole video. This should change in frequently.
  bodyAction: BodyAction; // Action that changes from time to time such as leaning forward to take another bite
  otherLabels: string[]; // List of other labels
  frameIndex: number; // Frame index
};

type Frame = {
  index: number; // Frame index
  timestamp: number; // Timestamp in the MOV file
  labels: Labels | null;
  isLabelled: boolean; // Whether the frame has been labelled
};

// Type for CSV data entries generated from motion data
type CSVData = {
  csvFilePath: string;
  movDataFilePath: string;
  motionDataFilePath: string;
  dateAdded: number; // Timestamp of when the data was added
  lastModified: number; // Timestamp of when the data was last modified
  rows: CsvRow[];
};

// Type for CSV row data entries with flattened structure
type CsvRow = {
  // General information
  timestamp: number; // Timestamp of the data

  // Frame data
  frameIndex: number; // Frame index
  frameTimestamp: number; // Timestamp in the MOV file
  isLabelled: boolean; // Whether the frame has been labeled

  // Labels
  isEating: boolean; // Indicates if eating is detected
  mouthState: MouthState; // State of the mouth (e.g., OPEN, CLOSED)
  isTalking: boolean; // Indicates if the person is talking
  primaryBodyState: PrimaryBodyState; // Primary body state (e.g., SITTING, STANDING)
  bodyAction: BodyAction; // Secondary body state (e.g., LEAN_FORWARD)
  otherLabels: string[]; // Other labels associated with the frame

  // Motion Data
  gravityX: number; // Gravity vector component in the x direction
  gravityY: number; // Gravity vector component in the y direction
  gravityZ: number; // Gravity vector component in the z direction
  transformedRotationX: number; // Transformed rotation quaternion component in the x direction
  transformedRotationY: number; // Transformed rotation quaternion component in the y direction
  transformedRotationZ: number; // Transformed rotation quaternion component in the z direction
  transformedRotationW: number; // Transformed rotation quaternion scalar component
  rotationRateX: number; // Rotation rate around the x axis
  rotationRateY: number; // Rotation rate around the y axis
  rotationRateZ: number; // Rotation rate around the z axis
  userAccelerationX: number; // User acceleration component in the x direction
  userAccelerationY: number; // User acceleration component in the y direction
  userAccelerationZ: number; // User acceleration component in the z direction
  attitudeRoll: number; // Roll angle in radians
  attitudePitch: number; // Pitch angle in radians
  attitudeYaw: number; // Yaw angle in radians
};

// Represents motion data captured from sensors at a specific timestamp
type MotionData = {
  timestamp: number; // The timestamp of the data sample
  gravity: {
    x: number; // Gravity vector component in the x direction
    y: number; // Gravity vector component in the y direction
    z: number; // Gravity vector component in the z direction
  };
  transformedRotation: {
    x: number; // Transformed rotation quaternion component in the x direction
    y: number; // Transformed rotation quaternion component in the y direction
    z: number; // Transformed rotation quaternion component in the z direction
    w: number; // Transformed rotation quaternion scalar component
  };
  rotationRate: {
    x: number; // Rotation rate around the x axis
    y: number; // Rotation rate around the y axis
    z: number; // Rotation rate around the z axis
  };
  userAcceleration: {
    x: number; // User acceleration component in the x direction
    y: number; // User acceleration component in the y direction
    z: number; // User acceleration component in the z direction
  };
  attitude: {
    roll: number; // Roll angle in radians
    pitch: number; // Pitch angle in radians
    yaw: number; // Yaw angle in radians
  };
};

type MovData = {
  movDataFilePath: string; // Path to the MOV file
  fps: number; // Frames per second
  numberOfFrames: number; // Number of frames in the MOV file
  duration: number; // Length of the video in milliseconds
  width: number; // Width of the video in pixels
  height: number; // Height of the video in pixels
};


type PointCoordinate = {
  x: number;
  y: number;
};


type Point = PointCoordinate & {
  id: number;
  location: "mouth" | "jaw"
};

type CanvasColors = {
  pointColor: string;
  lineColor: string;
  shapeFillColor: string;
  shapeStrokeColor: string;
};

type CanvasWithPoints = {
  id: number;
  title: string;
  color: CanvasColors;
  pointA: Point | null;
  pointB: Point | null;
  pointC: Point | null;
};

type CalculatedAreaResponse = {
  frame: number;
  timestamp: string;
  area: number;
};



type VideoPlaybackHandle = {
  playAllVideos: () => void;
  pauseAllVideos: () => void;
  setPlaybackSpeedForAll: (speed: number) => void;
  changeFrameForAll: (frames: number) => void;
  syncAllVideosTo: (timestamp: number) => void; // Add this line
  playerRefs: {
    [key: string]: React.RefObject<HTMLVideoElement>;
  };
};
