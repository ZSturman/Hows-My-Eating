import { ToggleGroup, ToggleGroupItem } from "../../components/ui/toggle-group";

// MarkerControlsOverlay renders the buttons to update the marker state.
interface MarkerControlsOverlayProps {
  mouthState: { mouth: "Open" | "Closed", action: "Bite" | "Chew" | "Swallow" | "Other"};
  setMarker: (params: {
    mouth?: "Open" | "Closed";
    action?: "Bite" | "Chew" | "Swallow" | "Other";
  }) => void;
}

const MarkerControlsOverlay: React.FC<MarkerControlsOverlayProps> = ({
  mouthState,
  setMarker,
}) => {
  return (
    <div className="bg-zinc-700/80 text-white p-2 rounded-md flex flex-row justify-evenly">
      <div className=" flex flex-col justify-center items-center gap-2">
        <h3>Mouth</h3>
        <ToggleGroup
          type="single"
          value={mouthState.mouth}
          className="flex items-start justify-start"
        >
          <ToggleGroupItem
            value="Open"
            aria-label="Teeth Open"
            onClick={() => setMarker({ mouth: "Open" })}
          >
            Open
          </ToggleGroupItem>
          <ToggleGroupItem
            value="Closed"
            aria-label="Teeth Closed"
            onClick={() => setMarker({ mouth: "Closed" })}
          >
            Closed
          </ToggleGroupItem>
        </ToggleGroup>
      </div>


      <div className=" flex flex-col justify-center items-center gap-2">
        <h3>Action</h3>
        <ToggleGroup
          type="single"
          value={mouthState.action}
          className="flex items-start justify-start"
        >
          <ToggleGroupItem
            value="Bite"
            aria-label="Bite"
            onClick={() => setMarker({ action: "Bite" })}
          >
            Bite
          </ToggleGroupItem>
          <ToggleGroupItem
            value="Chew"
            aria-label="Chew"
            onClick={() => setMarker({ action: "Chew" })}
          >
            Chew
          </ToggleGroupItem>
          <ToggleGroupItem
            value="Swallow"
            aria-label="Swallow"
            onClick={() => setMarker({ action: "Swallow" })}
          >
            Swallow
          </ToggleGroupItem>
          <ToggleGroupItem
            value="Other"
            aria-label="Other"
            onClick={() => setMarker({ action: "Other" })}
          >
            Other
          </ToggleGroupItem>

       
        </ToggleGroup>
      </div>
    </div>
  );
};

export default MarkerControlsOverlay;
