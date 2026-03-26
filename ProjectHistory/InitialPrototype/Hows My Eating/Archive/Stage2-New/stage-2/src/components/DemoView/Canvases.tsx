import { FaPlusCircle } from "react-icons/fa";
import CanvasWithDots from "./CanvasWithDots";
import { useState } from "react";
import { generatePreSetColor, generateRandomCanvasColors } from "./utils";

type CanvasesProps = {
  setCanvasesWithPoints: (canvases: CanvasWithPoints[]) => void;
  canvasesWithPoints: CanvasWithPoints[];
};

const Canvases: React.FC<CanvasesProps> = ({
  setCanvasesWithPoints,
  canvasesWithPoints,
}) => {
  const [lastIndex, setLastIndex] = useState<number>(2);

  const addCanvas = () => {
    const canvasId = lastIndex + 1;
    const newCanvas: CanvasWithPoints = {
      id: canvasId,
      title: "",
      color:
        canvasId > 4
          ? generateRandomCanvasColors()
          : generatePreSetColor(canvasId),
      pointA: null,
      pointB: null,
      pointC: null,
    };
    setCanvasesWithPoints([...canvasesWithPoints, newCanvas]);
    setLastIndex(canvasId);
  };

  const deleteCanvas = (canvasId: number) => {
    setCanvasesWithPoints(
      canvasesWithPoints.filter((canvas) => canvas.id !== canvasId)
    );
  };

  return (
    <div className="flex flex-row overflow-x-scroll overflow-y-hidden p-5 gap-8">
      {canvasesWithPoints.map((canvas) => (
        <div
          key={canvas.id}
          className={`rounded-lg relative group hover:shadow-lg hover:scale-105 transition-all duration-200`}
          style={{ border: `4px solid ${canvas.color.pointColor}` }}
        >
          <CanvasWithDots
            canvas={canvas}
            setCanvasesWithPoints={setCanvasesWithPoints}
            canvasesWithPoints={canvasesWithPoints}
          />
          <button
            onClick={() => deleteCanvas(canvas.id)}
            className={`absolute -top-3 -left-3 p-2 bg-gray-300 border-2 border-gray-500 text-gray-500 rounded-full hover:h-8 hover:w-8 h-6 w-6 flex items-center justify-center group-hover:opacity-100 opacity-0`}
          >
            X
          </button>
        </div>
      ))}

      <button
        onClick={addCanvas}
        className="p-2 flex flex-row items-center text-4xl justify-center opacity-60"
      >
        <FaPlusCircle />
      </button>
    </div>
  );
};

export default Canvases;