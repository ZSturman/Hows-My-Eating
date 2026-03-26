

/* export const initialSessionState: SessionState = {
  isDirty: false,
  logger: [],
  selectedDataRecord: null,
  selectedDataRecordFrames: null,
  selectedFrame: null,
  isPlaying: false,
  isImporting: false,
  isSyncing: false,
  isLoading: false,
  isSaving: false,
  isExporting: false,
}; */

import { AppRecord } from "../context/AppRecordContext";

export const initialAppRecord: AppRecord = {
  dataDirectories: [], 
  sessions: [],
  lastModified: Date.now(),
}


export const initialDataRecord: DataRecord = {
  id: Math.floor(Math.random() * 1000000),
  dateAdded: Date.now(),
  lastModified: Date.now(),
  dataDirectory: "",
  originalDataPath: "",
  exortPath: "",
  exportStatus: false,
  isLabelingComplete: false,
  isDataSynced: false,
  syncOffset: 0,
  movData: {
    path: "",
    duration: 0,
    width: 0,
    height: 0,
    fps: 0,
    totalFrames: 0,
  },
  motionData: {
    path: "",
    duration: 0,
    totalEntries: 0,
  },
  audioData: {
    path: "",
    duration: 0,
    channels: 0,
    sampleRate: 0,
  },
  csvData: {
    path: "",
    totalRows: 0,
  },
  labelsData: {
    path: "",
    labels: []
  }

};

