export const handleFileSystemEvent = async (event: { type: any; paths: string[] }) => {
    if (!event.paths || event.paths.length === 0) return;
  
    const eventType = event.type;
    const eventPath = event.paths[0];
  
    if (eventType.create?.kind === "folder") {
      console.log(`New folder created: ${eventPath}`, true);
      // Handle folder creation logic (e.g., track it for future monitoring)
    } else if (eventType.create?.kind === "file") {
      console.log(`New file created: ${eventPath}`, true);
  
      if (eventPath.endsWith(".json")) {
        console.log(`JSON file detected: ${eventPath}. Processing...`, true);
        // Load JSON data or process accordingly
      } else if (eventPath.endsWith(".mov")) {
        console.log(`Video file detected: ${eventPath}. Queuing for processing...`, true);
        // Handle video file (e.g., add it to processing queue)
      }
    } else if (eventType.modify?.kind === "data") {
      console.log(`File modified: ${eventPath}`, true);
  
      if (eventPath.includes("tracked-data.json")) {
        console.log("Tracked data JSON modified. Reloading data...", true);
        // Trigger a data reload or update operation
      }
    } else if (eventType.modify?.kind === "rename") {
      // Check if the "imported" folder was deleted or renamed
      if (eventPath.endsWith("/imported")) {
        console.log(`WARNING: The 'imported' folder was deleted or renamed: ${eventPath}`, true);
        // Additional handling could be added here (e.g., attempt recovery, notify user)
      }
    } else {
      console.log(`Unhandled file system event: ${JSON.stringify(event, null, 2)}`, true);
    }
  };