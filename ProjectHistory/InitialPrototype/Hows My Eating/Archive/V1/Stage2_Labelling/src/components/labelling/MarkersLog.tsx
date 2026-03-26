import { Marker } from "@/types/Markers";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "../../components/ui/accordion";

// MarkersLog displays a scrollable log of all markers.
interface MarkersLogProps {
  markers: Marker[];
}

const MarkersLog: React.FC<MarkersLogProps> = ({ markers }) => {
  return (
    <div className="w-full max-w-2xl mx-auto p-4">
      <Accordion type="single" collapsible className="w-full">
        <AccordionItem value="markers">
          <AccordionTrigger>Markers Log</AccordionTrigger>
          <AccordionContent>
            <div>
              {markers.map((marker) => (
                <LogEntry key={marker.id} marker={marker} />
              ))}
            </div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </div>
  );
};

export default MarkersLog;

const LogEntry = ({ marker }: { marker: Marker }) => {
  return (
    <div className="mb-1">
      <div>
        Frame: {marker.frame} - Timestamp: ({marker.timestamp}s)
      </div>
      <div>
        <span className="font-bold">{marker.mouth}</span> -{" "}
        <span className="font-bold">{marker.action}</span>{" "}
      </div>
    </div>
  );
};
