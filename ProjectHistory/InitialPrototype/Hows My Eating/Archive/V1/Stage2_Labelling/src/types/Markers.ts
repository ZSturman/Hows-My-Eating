export interface Marker {
    id: number;
    frame: number;
    timestamp: number;
    mouth: "Open" | "Closed"
    action: "Bite" | "Chew" | "Swallow" | "Other"
    needsVerification?: boolean
  }

export type VideoChunkStatus = {
  fileName: string;
  filePath: string;
  originalValue: "Bite" | "Chew" | "Swallow" | "Other";
  frameStart: number;
  frameEnd: number;
  verified: boolean
  correct: boolean
  relabelled: number[]
};