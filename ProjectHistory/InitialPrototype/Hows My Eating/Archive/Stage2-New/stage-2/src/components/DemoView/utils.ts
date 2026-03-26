import { resolveResource } from "@tauri-apps/api/path";
import { Command } from "@tauri-apps/api/shell";

  
export async function calculateArea(triangle: CanvasWithPoints): Promise<CalculatedAreaResponse[] | null> {
  if (!triangle.pointA || !triangle.pointB || !triangle.pointC) {
    console.error('Invalid triangle points', triangle);
    return null;
  }

  // Construct point names based on their location and id
  const pointA = `${triangle.pointA.location.charAt(0).toUpperCase()}${triangle.pointA.location.slice(1)}_${triangle.pointA.id}`;
  const pointB = `${triangle.pointB.location.charAt(0).toUpperCase()}${triangle.pointB.location.slice(1)}_${triangle.pointB.id}`;
  const pointC = `${triangle.pointC.location.charAt(0).toUpperCase()}${triangle.pointC.location.slice(1)}_${triangle.pointC.id}`;

  const csvFilePath = "/Users/zacharysturman/Desktop/Stage2-New/stage-2/public/demo/features.csv";

  try {
    // Resolve the path to the executable
    console.log('Running executable to calculate area...');
    await resolveResource('bin/calculate_areas');
    const command = Command.sidecar('bin/calculate_areas', [csvFilePath, pointA, pointB, pointC]);
    
    const output = await command.execute();

    if (output.code === 0) {
      console.log('Executable output:', output.stdout);
      // Parse output to an array of calculated areas
      const infoArray = JSON.parse(output.stdout.trim()) as Array<{ Frame: string, Timestamp: string, Area: number }>;

      // Map the parsed JSON to match the `CalculatedAreaResponse` type
      const returnedData: CalculatedAreaResponse[] = infoArray.map(info => ({
        frame: parseInt(info.Frame, 10),  // Convert 'Frame' to a number
        timestamp: info.Timestamp,
        area: info.Area,
      }));

      console.log('Calculated areas:', returnedData);
      return returnedData;
    } else {
      console.error('Error running executable:', output.stderr);
      return null;
    }
  } catch (error) {
    console.error('Error calculating area:', error);
    return null;
  }
}

export function generateRandomCanvasColors() {
  // Generate a random hue between 0 and 360
  const hue = Math.floor(Math.random() * 360);

  // Define the saturation and lightness values for each color property
  const saturation = 100;
  const pointLightness = 50;
  const lineLightness = 30;
  const fillLightness = 70;
  const fillOpacity = 0.2;
  const strokeLightness = 40;

  // Return an object with the generated colors
  return {
    pointColor: `hsl(${hue}, ${saturation}%, ${pointLightness}%)`,
    lineColor: `hsl(${hue}, ${saturation}%, ${lineLightness}%)`,
    shapeFillColor: `hsla(${hue}, ${saturation}%, ${fillLightness}%, ${fillOpacity})`,
    shapeStrokeColor: `hsl(${hue}, ${saturation}%, ${strokeLightness}%)`,
  };
}


export type PresetColors = {
  [key: number]: {
    h: number;
    s: number;
    l: number;
  };
};

export const generatePreSetColor = (canvasId: number) => {
  const presetColors: PresetColors = {
    1: {
      h: 168,
      s: 63,
      l: 75,
    },
    2: {
      h: 22,
      s: 63,
      l: 75,
    },
    3: {
      h: 248,
      s: 63,
      l: 75,
    },
    4: {
      h: 123,
      s: 20,
      l: 57,
    },
  };

  const { h: hue, s: saturation } = presetColors[canvasId];
  const pointLightness = 50;
  const lineLightness = 30;
  const fillLightness = 70;
  const fillOpacity = 0.7;
  const strokeLightness = 25;

  return {
    pointColor: `hsl(${hue}, ${saturation}%, ${pointLightness}%)`,
    lineColor: `hsl(${hue}, ${saturation}%, ${lineLightness}%)`,
    shapeFillColor: `hsla(${hue}, ${saturation}%, ${fillLightness}%, ${fillOpacity})`,
    shapeStrokeColor: `hsl(${hue}, ${saturation}%, ${strokeLightness}%)`,
  };
};