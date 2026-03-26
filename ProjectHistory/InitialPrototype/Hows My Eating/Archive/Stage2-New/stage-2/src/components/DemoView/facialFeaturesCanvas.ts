const CANVAS_WIDTH = 400;
const CANVAS_HEIGHT = 300;

const centerX = CANVAS_WIDTH / 2;
let centerY = CANVAS_HEIGHT / 3;
const radius = 150;

export const canvasDimensions = { width: CANVAS_WIDTH, height: CANVAS_HEIGHT, centerX, centerY, radius };

// Function to generate jawline points with flipped IDs
const generateJawlinePoints = (numPoints: number): Point[] => {
  const points: Point[] = [];
  for (let i = 0; i < numPoints; i++) {
    const angle = Math.PI * (i / (numPoints - 1));
    const x = centerX + radius * Math.cos(angle);
    const y = centerY + radius * Math.sin(angle);
    // Assign IDs in reverse order (numPoints - i) to flip the ID order
    points.push({ id: numPoints - i, location: "jaw", x, y });
  }
  return points;
};

// Generate jawline points (IDs 1-17 flipped)
const jawlinePoints = generateJawlinePoints(17);

centerY += 20;

// Define mouth points with specific IDs (IDs 49-68)
const mouthPoints: Point[] = [
  { id: 52, location: "mouth", x: centerX, y: centerY - 20 }, // Point 52 (top center)
  { id: 63, location: "mouth", x: centerX, y: centerY - 5 },  // Point 63
  { id: 67, location: "mouth", x: centerX, y: centerY + 7 },  // Point 67
  { id: 58, location: "mouth", x: centerX, y: centerY + 25 }, // Point 58 (bottom center)
  { id: 51, location: "mouth", x: centerX - 20, y: centerY - 25 }, // Point 51 (left center line)
  { id: 62, location: "mouth", x: centerX - 20, y: centerY - 5 },  // Point 62
  { id: 68, location: "mouth", x: centerX - 20, y: centerY + 7 },  // Point 68
  { id: 59, location: "mouth", x: centerX - 20, y: centerY + 25 }, // Point 59
  { id: 53, location: "mouth", x: centerX + 20, y: centerY - 25 }, // Point 53 (right center line)
  { id: 64, location: "mouth", x: centerX + 20, y: centerY - 5 },  // Point 64
  { id: 66, location: "mouth", x: centerX + 20, y: centerY + 7 },  // Point 66
  { id: 57, location: "mouth", x: centerX + 20, y: centerY + 25 }, // Point 57
  { id: 50, location: "mouth", x: centerX - 40, y: centerY - 20 }, // Point 50 (second left line)
  { id: 61, location: "mouth", x: centerX - 40, y: centerY + 0 },  // Point 61
  { id: 60, location: "mouth", x: centerX - 40, y: centerY + 20 }, // Point 60
  { id: 54, location: "mouth", x: centerX + 40, y: centerY - 20 }, // Point 54 (second right line)
  { id: 65, location: "mouth", x: centerX + 40, y: centerY + 0 },  // Point 65
  { id: 56, location: "mouth", x: centerX + 40, y: centerY + 20 }, // Point 56
  { id: 49, location: "mouth", x: centerX - 60, y: centerY },      // Point 49 (far left)
  { id: 55, location: "mouth", x: centerX + 60, y: centerY },      // Point 55 (far right)
];

const allPoints = [...jawlinePoints, ...mouthPoints];

export { allPoints, jawlinePoints, mouthPoints };