import React, { useState, useRef, useEffect, MouseEvent } from "react";
import { allPoints } from "./facialFeaturesCanvas";

type CanvasWithDotsProps = {
  canvas: CanvasWithPoints;
  setCanvasesWithPoints: (canvases: CanvasWithPoints[]) => void;
  canvasesWithPoints: CanvasWithPoints[];
};

const CanvasWithDots: React.FC<CanvasWithDotsProps> = ({
  canvas,
  setCanvasesWithPoints,
  canvasesWithPoints,
}) => {
  const [currentCanvas, setCurrentCanvas] = useState<CanvasWithPoints>(canvas);
  const [hoveredPoint, setHoveredPoint] = useState<Point | null>(null);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    setCurrentCanvas(canvas); // Ensure currentCanvas is set to the prop canvas on render
  }, [canvas]);

  useEffect(() => {
    const canvasEl = canvasRef.current;
    if (!canvasEl) return;

    const ctx = canvasEl.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, canvasEl.width, canvasEl.height);

    const { pointColor, lineColor, shapeFillColor, shapeStrokeColor } =
      currentCanvas.color;

    allPoints.forEach((point) => {
      if (!point) {
        console.error("Undefined point or missing coordinates:", point);
      } else {
        const isSelected =
          (currentCanvas.pointA && currentCanvas.pointA.id === point.id) ||
          (currentCanvas.pointB && currentCanvas.pointB.id === point.id) ||
          (currentCanvas.pointC && currentCanvas.pointC.id === point.id);

        // Draw outer circle for the point
        ctx.beginPath();
        ctx.arc(point.x, point.y, 5, 0, 2 * Math.PI);
        ctx.fillStyle = isSelected ? lineColor : pointColor;
        ctx.fill();

        if (isSelected) {
          // Draw inner border for the selected point
          ctx.beginPath();
          ctx.arc(point.x, point.y, 3, 0, 2 * Math.PI);
          ctx.strokeStyle = "white";
          ctx.lineWidth = 2;
          ctx.stroke();
        }

        // Draw hover effect if hovering over this point
        if (hoveredPoint && hoveredPoint.id === point.id) {
          ctx.beginPath();
          ctx.arc(point.x, point.y, 7, 0, 2 * Math.PI);
          ctx.strokeStyle = "yellow"; // Color for hover effect
          ctx.lineWidth = 2;
          ctx.stroke();
        }
      }
    });

    const filledPoints = [
      currentCanvas.pointA,
      currentCanvas.pointB,
      currentCanvas.pointC,
    ].filter((point) => point !== null) as Point[];

    // Draw lines between selected points
    if (filledPoints.length === 2) {
      ctx.beginPath();
      ctx.moveTo(filledPoints[0].x, filledPoints[0].y);
      ctx.lineTo(filledPoints[1].x, filledPoints[1].y);
      ctx.strokeStyle = lineColor;
      ctx.stroke();
    }

    // Draw the triangle if all points are filled
    if (filledPoints.length === 3) {
      ctx.beginPath();
      ctx.moveTo(filledPoints[0].x, filledPoints[0].y);
      ctx.lineTo(filledPoints[1].x, filledPoints[1].y);
      ctx.lineTo(filledPoints[2].x, filledPoints[2].y);
      ctx.closePath();
      ctx.fillStyle = shapeFillColor;
      ctx.fill();
      ctx.strokeStyle = shapeStrokeColor;
      ctx.stroke();
    }
  }, [currentCanvas, hoveredPoint]); // Include hoveredPoint in dependencies to redraw on hover

  const handleCanvasClick = (event: MouseEvent<HTMLCanvasElement>) => {
    const canvasEl = canvasRef.current;
    if (!canvasEl) return;

    const rect = canvasEl.getBoundingClientRect();
    const scrollLeft = window.scrollX || document.documentElement.scrollLeft;
    const scrollTop = window.scrollY || document.documentElement.scrollTop;
    const scaleX = canvasEl.width / rect.width;
    const scaleY = canvasEl.height / rect.height;
    const clickX = (event.clientX - rect.left + scrollLeft) * scaleX;
    const clickY = (event.clientY - rect.top + scrollTop) * scaleY;

    const clickedPoint = allPoints.find(
      (point) => Math.hypot(point.x - clickX, point.y - clickY) < 10
    );

    if (!clickedPoint) {
      console.log("No point clicked");
      return;
    }

    console.log(`Clicked point coordinates: (${clickedPoint.x}, ${clickedPoint.y})`);

    const localPoints = [
      currentCanvas.pointA,
      currentCanvas.pointB,
      currentCanvas.pointC,
    ];
    const isPointSelected = localPoints.some(
      (point) => point && point.id === clickedPoint.id
    );

    let updatedCanvas: CanvasWithPoints;

    if (isPointSelected) {
      console.log("Point already selected, deselecting");
      const updatedPoints = localPoints.map((point) =>
        point && point.id === clickedPoint.id ? null : point
      ) as [Point | null, Point | null, Point | null];

      updatedCanvas = {
        ...currentCanvas,
        pointA: updatedPoints[0],
        pointB: updatedPoints[1],
        pointC: updatedPoints[2],
      };
    } else if (localPoints.filter((p) => p !== null).length < 3) {
      console.log("Selecting point");
      const updatedPoints = [...localPoints] as [
        Point | null,
        Point | null,
        Point | null
      ];
      for (let i = 0; i < updatedPoints.length; i++) {
        if (updatedPoints[i] === null) {
          updatedPoints[i] = clickedPoint;
          break;
        }
      }
      updatedCanvas = {
        ...currentCanvas,
        pointA: updatedPoints[0],
        pointB: updatedPoints[1],
        pointC: updatedPoints[2],
      };
    } else {
      return;
    }

    setCurrentCanvas(updatedCanvas);

    const updatedCanvases = canvasesWithPoints.map((c) =>
      c.id === updatedCanvas.id ? updatedCanvas : c
    );
    setCanvasesWithPoints(updatedCanvases);
  };

  const handleMouseMove = (event: MouseEvent<HTMLCanvasElement>) => {
    const canvasEl = canvasRef.current;
    if (!canvasEl) return;

    const rect = canvasEl.getBoundingClientRect();
    const scrollLeft = window.scrollX || document.documentElement.scrollLeft;
    const scrollTop = window.scrollY || document.documentElement.scrollTop;
    const scaleX = canvasEl.width / rect.width;
    const scaleY = canvasEl.height / rect.height;
    const mouseX = (event.clientX - rect.left + scrollLeft) * scaleX;
    const mouseY = (event.clientY - rect.top + scrollTop) * scaleY;

    const hoveredPoint = allPoints.find(
      (point) => Math.hypot(point.x - mouseX, point.y - mouseY) < 10
    );

    setHoveredPoint(hoveredPoint || null);
  };

  const handleMouseLeave = () => {
    setHoveredPoint(null);
  };

  return (
    <div className="relative">
      <canvas
        ref={canvasRef}
        width={400}
        height={300}
        onClick={handleCanvasClick}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        className="rounded-md"
      />
    </div>
  );
};

export default CanvasWithDots;