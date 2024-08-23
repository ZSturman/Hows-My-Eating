import { useEffect, useState } from "react";
import { checkRequiredFiles } from "../utils/import";
import { readJson } from "../utils/readJson";

type TrackingJsonProps = {
    selectedDataPath: string;
}

const TrackingJson: React.FC<TrackingJsonProps> = ({ selectedDataPath }) => {
    const [trackingJson, setTrackingJson] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const processFiles = async () => {
            try {
                if (typeof selectedDataPath !== "string" || !selectedDataPath.trim()) {
                    setError("Invalid directory path.");
                    return;
                }

                const { hasTrackingJson } = await checkRequiredFiles(selectedDataPath);

                console.log("File Check:", { hasTrackingJson }); // Add logging

                if (!hasTrackingJson) {
                    setError("Directory must contain a .json file.");
                    return;
                }

                if (hasTrackingJson) {
                    const trackingJsonPath = `${selectedDataPath}/${hasTrackingJson}`;
                    console.log("Tracking JSON Path:", trackingJsonPath); // Log the file path
                    const trackingJson = await readJson(trackingJsonPath);
                    if (trackingJson) {
                        setTrackingJson(trackingJson);
                    } else {
                        setError("Failed to parse tracking JSON.");
                    }
                }
            } catch (error) {
                console.error("Error processing files:", error);
                setError("Error processing files.");
            } finally {
                setLoading(false);
            }
        };

        processFiles();
    }, [selectedDataPath]);

    return (
        <div >
            {loading && <div>Loading...</div>}
            {error && <div className="text-red-500">{error}</div>}
            {trackingJson && (
                <div className="text-xs">
                    <pre>{JSON.stringify(trackingJson, null, 2)}</pre>
                </div>
            )}
        </div>
    );
}

export default TrackingJson