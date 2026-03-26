export type NewImportedData = {
  originalImportedFolderPath: string;
  originalImportedFolderName: string;
  originalMovFilePath: string;
  originalMotionDataJsonFilePath: string;
  imported: Date;
  importedFolderPath: string;
  importedFolderName: string;
};

export type MovInfo = {
  videoPath: string;
  duration?: number;
  width?: number;
  height?: number;
  fps?: number;
  totalFrames?: number;
};

export type BaseStepOutput = {
  started: Date;
  completed: Date | null;
};

export type CollectMovInfoOutput = BaseStepOutput & {
  movInfoFilePath: string;
  mainThumbnailPath: string;
  scrubbingThumbnailsPaths: string[];
};

export type ProcessVisualsOutput = BaseStepOutput & {
  pointsDataCsvFilePath: string;
  outputVideoFilePath: string | null;
};

export type ComputeRatiosOutput = BaseStepOutput & {
  ratiosCsvFilePath: string;
};

export type ManualLabelingOutput = BaseStepOutput & {
  manuallyLabeledJsonFilePath: string;
};

export type MergeLabelsAndCsvOutput = BaseStepOutput & {
  mergedCsvFilePath: string;
};

export type VerifiedOutputs = BaseStepOutput;
export type ExportDataOutputs = BaseStepOutput & {
  exportedDirectoryPath: string;
};

export type StepOutput =
  | CollectMovInfoOutput
  | ProcessVisualsOutput
  | ComputeRatiosOutput
  | ManualLabelingOutput
  | MergeLabelsAndCsvOutput
  | VerifiedOutputs
  | ExportDataOutputs;

export type ChewingDataState = {
  id: string;
  originalImportedFolderPath: string;
  originalImportedFolderName: string;
  originalMovFilePath: string;
  originalMotionDataJsonFilePath: string;
  imported: Date;
  importedFolderPath: string;
  importedFolderName: string;
  movInfo: MovInfo | null 
  collectMovInfo: CollectMovInfoOutput | null 
  processVisuals: ProcessVisualsOutput | null 
  computeRatios: ComputeRatiosOutput | null 
  manualLabeling: ManualLabelingOutput | null 
  mergeLabelsAndCsv: MergeLabelsAndCsvOutput | null 
  verifyData: VerifiedOutputs | null 
  exportData: ExportDataOutputs | null 
  currentPipelineStep: number 
  error?: string
}

export const defaultChewingDataState: ChewingDataState = {
  id: "",
  originalImportedFolderPath: "",
  originalImportedFolderName: "",
  originalMovFilePath: "",
  originalMotionDataJsonFilePath: "",
  imported: new Date(),
  importedFolderPath: "",
  importedFolderName: "",
  movInfo: null,
  collectMovInfo: null,
  processVisuals: null,
  computeRatios: null,
  manualLabeling: null,
  mergeLabelsAndCsv: null,
  verifyData: null,
  exportData: null,
  currentPipelineStep: 0,
}
