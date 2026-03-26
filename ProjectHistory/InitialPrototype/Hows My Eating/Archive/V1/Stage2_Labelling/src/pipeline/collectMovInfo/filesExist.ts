import {
  ChewingDataState,
  CollectMovInfoOutput,
} from "@/types/ChewingData.types";

const collectMovInfoFilesExist = async (
  data: ChewingDataState,
  appConfig: AppConfig
): Promise<ReturnStatus<CollectMovInfoOutput>> => {
  try {
    const items = data.collectMovInfo;
    console.log("[collectMovInfoFilesExist] items", items);

    if (!items) {
      return {
        status: "error",
        data: "No collectMovInfo data found",
      };
    }

    if (!items.movInfoFilePath) {
      return {
        status: "error",
        data: "No movInfoFilePath found in collectMovInfo data",
      };
    }

    if (appConfig.requireMainVideoThumbnail && !items.mainThumbnailPath) {
      return {
        status: "error",
        data: "No mainThumbnailPath found in collectMovInfo data",
      };
    }

    if (
      appConfig.requireScrubbingThumbnails &&
      !items.scrubbingThumbnailsPaths
    ) {
      return {
        status: "error",
        data: "No scrubbingThumbnailsPath found in collectMovInfo data",
      };
    }

    return {
      status: "success",
      data: items,
    };
  } catch (error) {
    return {
      status: "error",
      data: `Error checking for collectMovInfo files: ${error}`,
    };
  }
};

export default collectMovInfoFilesExist;
