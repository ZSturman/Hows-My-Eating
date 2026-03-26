// ...existing imports...
import { join } from "@tauri-apps/api/path";
import { Command } from "@tauri-apps/plugin-shell";
import { exists } from "@tauri-apps/plugin-fs";

// Import functions under test
import { runProcessVisuals } from "../../pipeline/commands/processVisuals";
import { runMergeLabels } from "../../pipeline/commands/merge";
import { runExport } from "../../pipeline/commands/exporting";
import { runComputeRatios } from "../../pipeline/commands/computeRatios";
import { runCollectMovInfo } from "../../pipeline/commands/collectMovInfo";
import { runGetChunks } from "../../pipeline/commands/chunks";
import collectMovInfoFileValidations from "../../pipeline/collectMovInfo/fileValidations";
import collectMovInfoFilesExist from "../../pipeline/collectMovInfo/filesExist";
import { checkMovInfo } from "../../pipeline/checks/movInfo";
import { checkInitialDataImports } from "../../pipeline/checks/initialDataImports";

// Mocks for external dependencies
jest.mock("@tauri-apps/plugin-shell", () => ({
  Command: {
    sidecar: jest.fn(() => ({
      execute: jest.fn(async () => ({
        stdout: '{"success":true, "data": {"csv_file": "test.csv", "video_file": "test.mp4", "merged_csv": "merged.csv"}}',
        stderr: ""
      }))
    }))
  }
}));

jest.mock("@tauri-apps/api/path", () => ({
  join: jest.fn((...args: any[]) => args.join("/"))
}));

jest.mock("@tauri-apps/plugin-fs", () => ({
  exists: jest.fn(async (path: string) => true),
  readTextFile: jest.fn(async (path: string) => '{"key": "value"}')
}));

// Dummy sanitizer
jest.mock("../../pipeline/utilities/commands", () => ({
  sanitizeArg: (arg: string) => arg,
  filterStderr: (input: string) => input,
  parseJsonResponse: <T>(stdout: string) => {
    const startIndex = stdout.indexOf('{"success":');
    return JSON.parse(stdout.slice(startIndex));
  }
}));

describe("Pipeline Commands Tests", () => {
  describe("runProcessVisuals", () => {
    it("should return error for invalid outputVideo", async () => {
      const result = await runProcessVisuals("dummyDir", "dummy.csv", "maybe");
      expect(result.status).toBe("error");
    });

    it("should return success when valid", async () => {
      const result = await runProcessVisuals("dummyDir", "dummy.csv", "True");
      expect(result.status).toBe("success");
      expect(result.data.csv_file_path).toBe("test.csv");
    });
  });

  describe("runMergeLabels", () => {
    it("should return success with merged_csv", async () => {
      const result = await runMergeLabels("dummyDir", "dummy.json", "movInfo.txt", "output.csv");
      expect(result.status).toBe("success");
      expect(result.data.merged_csv_path).toBe("test.csv"); // test.csv from JSON data mapped from function expecting merged_csv
    });
  });

  describe("runExport", () => {
    it("should return true on success", async () => {
      const result = await runExport("dummyDataPath", "dummyExport", "motion.json", "mov.txt", "ratios.csv", "points.csv", "merged.csv", "chunksDir", "chunksRec");
      expect(result).toBe(true);
    });
  });

  describe("runComputeRatios", () => {
    it("should return success for compute ratios", async () => {
      const result = await runComputeRatios("dummyDir", "points.csv", "compare.csv");
      expect(result.status).toBe("success");
      expect(result.data.csv_file_path).toBe("test.csv");
    });
  });

  describe("runCollectMovInfo", () => {
    it("should return success when valid", async () => {
      const result = await runCollectMovInfo("dummyDir", "movInfo.json");
      expect(result.status).toBe("success");
    });
  });

  describe("runGetChunks", () => {
    it("should return success for chunk generation", async () => {
      const result = await runGetChunks("dummyDir", "video.mp4", "merged.csv", "outputDir");
      expect(result.status).toBe("success");
      if (typeof result.data !== "string") {
        expect(result.data.chunksFolderPath).toBe("merged.csv");
      }
    });
  });
});

describe("Pipeline Validations Tests", () => {
  describe("collectMovInfoFileValidations", () => {
    it("should return error if movInfo is null and file cannot be parsed", async () => {
      // Overriding exists to return false for this test
      const { exists } = require("@tauri-apps/plugin-fs");
      exists.mockImplementationOnce(async () => false);
      const result = await collectMovInfoFileValidations(null, { movInfoFilePath: "invalid.json", mainThumbnailPath: "", scrubbingThumbnailsPaths: [], started: new Date(), completed: new Date() }, true, false);
      expect(result.status).toBe("error");
    });
  });

  describe("collectMovInfoFilesExist", () => {
    it("should return error when required properties are missing", async () => {
      const result = await collectMovInfoFilesExist({
        id: "dummyId",
        originalImportedFolderPath: "dummyFolder",
        originalImportedFolderName: "dummyFolderName",
        originalMovFilePath: "dummyMovFilePath",
        originalMotionDataJsonFilePath: "dummyMotionDataJsonFilePath",
        imported: new Date(),
        importedFolderPath: "dummyImportedFolderPath",
        importedFolderName: "dummyImportedFolderName",
        movInfo: null,
        collectMovInfo: {
          movInfoFilePath: "dummyPath",
          mainThumbnailPath: "dummyPath",
          scrubbingThumbnailsPaths: [],
          started: new Date(),
          completed: new Date()
        },
        processVisuals: null,
        computeRatios: null,
        manualLabeling: null,
        mergeLabelsAndCsv: null,
        exportData: null,
        getChunks: null
      }, { requireMainVideoThumbnail: true, requireScrubbingThumbnails: true });
      expect(result.status).toBe("error");
    });
  });

  describe("checkMovInfo", () => {
    it("should return error if movInfoFilePath is missing", async () => {
      const result = await checkMovInfo(null, { movInfoFilePath: "" , mainThumbnailPath:"", scrubbingThumbnailsPaths: []}, false, false);
      expect(result.status).toBe("error");
    });
  });

  describe("checkInitialDataImports", () => {
    it("should return true when folder exists and contains files", async () => {
      const dummyData = {
        originalImportedFolderPath: "dummyFolder",
        originalMovFilePath: "movie.mp4",
        originalMotionDataJsonFilePath: "data.json"
      };
      const result = await checkInitialDataImports(dummyData);
      expect(result).toBe(true);
    });
  });
});
