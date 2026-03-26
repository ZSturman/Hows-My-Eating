import { MovInfo } from "../../types/ChewingData.types";

export type ProcessVisualsReturnedData = {
  csv_file_path: string;
  video_file_path: string | null;
};

export type ComputeRatiosReturnedData = {
  csv_file_path: string;
};

export type CollectMovInfoReturnedData = {
  mov_info: MovInfo;
  mov_info_file_path: string;
  main_thumbnail_path: string;
  scrubbing_thumbnails_paths: string[];
};

export type MergeLabelsReturnedData = {
  merged_csv_path: string;
}

export type ChunksReturnedData = {
  chunksFolderPath: string;
}

export type CommandReturnData =
  | CollectMovInfoReturnedData
  | ComputeRatiosReturnedData
  | ProcessVisualsReturnedData 
  | MergeLabelsReturnedData
  | ChunksReturnedData;
