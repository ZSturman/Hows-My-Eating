HOWS MY EATING - archive / reference 

## Hook Implementations

### **Core Custom Hooks**
1. **`useIsProcessingRef`** – Track processing status without causing re-renders.
2. **`useLoadChewingDataStateFromJson`** – Handle fetching chewing data state from a JSON file.
3. **`useAttachDragDropListener`** – Manage event listener for `tauri://drag-drop`.
4. **`useHandleDroppedPath`** – Process dropped directory paths and validate contents.
5. **`useCopyFilesToAppDataDir`** – Copy necessary files to the app data directory.
6. **`useLoadDataFromJson`** – Load and parse tracked data from JSON.
7. **`useSaveDataToJson`** – Handle saving chewing data state to JSON.
8. **`useImportNewData`** – Manage the addition of new imported data.
9. **`useRemoveDataFromJson`** – Remove chewing data state from JSON.
10. **`useRemoveDataFromAppDataDir`** – Delete associated files and directories.
11. **`useGetDataBaseStepOutputValues`** – Retrieve step output values.
12. **`useGetRequiredCommandInputs`** – Determine required inputs for pipeline steps.
13. **`useRunPipelineCommand`** – Execute pipeline steps via Tauri commands.
14. **`useValidatePipelineProcessOutput`** – Validate pipeline step outputs.
15. **`useHandleCollectedMovInfoDataOutput`** – Handle and validate `Collect Mov Info` output.
16. **`useHandleProcessVisualsDataOutput`** – Handle and validate `Process Visuals` output.
17. **`useHandleComputeRatiosDataOutput`** – Handle and validate `Compute Ratios` output.
18. **`useHandleUpdateDataValues`** – Update state with validated pipeline step output.
19. **`useHandleCommandOutputData`** – Process command output and update chewing data state.
20. **`usePipelineProgression`** – Manage advancing through the pipeline steps.
21. **`useAddPipelineStepStartTimestamp`** – Record timestamps when steps begin.
22. **`useUpdateChewDataParametersWithPipelineStepOutputAndCompletedTimestamp`** – Update step completion timestamps.
23. **`useStopCurrentProcess`** – Handle stopping the processing of a pipeline step.
24. **`useExportChewData`** – Handle exporting processed data.

---

## Context Provider Functions

### **Primary Context Functions**

1. **`initializeChewingDataState`**
   - **Purpose:** Initializes and loads the chewing data state from JSON.
   - **How:** Calls `useLoadChewingDataStateFromJson` and updates the state.

2. **`handleDroppedPath`**
   - **Purpose:** Processes a dropped directory path by validating its contents.
   - **How:** Calls `useHandleDroppedPath` to check for required files and import the data.

3. **`copyFilesToAppDataDir`**
   - **Purpose:** Copies necessary files (e.g., `.json`, `.mov`) to the app’s data directory.
   - **How:** Calls `useCopyFilesToAppDataDir`, returning the new directory path or `false` on failure.

4. **`importNewData`**
   - **Purpose:** Adds a new dataset entry after validating imported files.
   - **How:** Calls `useImportNewData` to create and append a new `ChewingDataState` object.

5. **`removeDataEntry`**
   - **Purpose:** Removes a dataset from both state and persistent storage.
   - **How:** Calls `useRemoveDataFromJson` and `useRemoveDataFromAppDataDir` to handle deletion.

6. **`fetchStepStartAndCompletionStatus`**
   - **Purpose:** Checks whether a pipeline step has started or completed for a given dataset.
   - **How:** Calls `useGetDataBaseStepOutputValues` to retrieve timestamps.

7. **`fetchStepOutputData`**
   - **Purpose:** Retrieves the stored output of a specific pipeline step.
   - **How:** Calls `useGetDataBaseStepOutputValues` and returns the step’s saved output.

8. **`fetchRequiredStepInputs`**
   - **Purpose:** Determines the input data required to execute a given pipeline step.
   - **How:** Calls `useGetRequiredCommandInputs` to return necessary file paths or parameters.

9. **`executePipelineStep`**
   - **Purpose:** Runs the appropriate command for a pipeline step and processes its output.
   - **How:**
     - Calls `useRunPipelineCommand` to execute the step.
     - Calls `useValidatePipelineProcessOutput` to validate the output.
     - Updates state with the result.

10. **`processPipelineCommandOutput`**
    - **Purpose:** Validates and updates state with the output of a completed pipeline step.
    - **How:**
      - Calls `useValidatePipelineProcessOutput` to confirm correctness.
      - Calls `useHandleCommandOutputData` to update state with the validated data.

11. **`advanceToNextStep`**
    - **Purpose:** Moves the dataset to the next step in the pipeline.
    - **How:** Calls `usePipelineProgression` to update the current step and trigger the next process if applicable.

12. **`recordStepStartTime`**
    - **Purpose:** Logs the start time for a pipeline step.
    - **How:** Calls `useAddPipelineStepStartTimestamp` and updates the dataset.

13. **`updateChewingDataStateWithStepOutput`**
    - **Purpose:** Updates the dataset’s parameters with the processed step’s output and completion timestamp.
    - **How:** Calls `useUpdateChewDataParametersWithPipelineStepOutputAndCompletedTimestamp`.

14. **`haltCurrentProcess`**
    - **Purpose:** Stops the ongoing process and resets relevant flags.
    - **How:** Calls `useStopCurrentProcess`, clearing the processing state.

15. **`exportProcessedData`**
    - **Purpose:** Triggers data export functionality for a dataset.
    - **How:** Calls `useExportChewData` to handle exporting.

---

## **State Management Best Practices**
### **Key Optimizations:**
- Use `useRef` for values that don't need re-renders.
- Batch state updates to avoid unnecessary renders.
- Use `Map` instead of arrays for faster lookups.
- Consider memoization (`useMemo`) where applicable.

---

## **Handling Error States & Recovery**
- Implement a **global error handler** using `usePipelineErrorHandler`.
- Provide **automatic retry logic** for recoverable errors.
- Ensure **graceful rollbacks** if a step fails.

---

## **Pipeline Dependency Management**
- Ensure **steps only run** if all dependencies are met.
- Provide **clear feedback** if dependencies are missing.
- Implement **parallel execution** where applicable.

---

## **Tauri-Specific Considerations**
- Handle **file system access permissions** properly.
- Clean up **Tauri event listeners** to avoid memory leaks.
- Ensure **cross-platform compatibility** for filesystem operations.

---

This structured document provides clear and well-organized notes for implementing the Tauri pipeline system efficiently.

