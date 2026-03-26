import { generatePreSetColor } from "./utils";


const defaultCanvas1A: CanvasWithPoints = {
  id: 1,
  title: "",
  color: generatePreSetColor(1),
  pointA: {
    id: 49,
    location: "mouth",
    x: 140,
    y: 120,
  },
  pointB: {
    id: 55,
    location: "mouth",
    x: 260,
    y: 120,
  },
  pointC: {
    id: 9,
    location: "jaw",
    x: 200,
    y: 250,
  },
};

const defaultCanvas1B: CanvasWithPoints = {
  id: 2,
  title: "",
  color: generatePreSetColor(2),
  pointA: {
    id: 1,
    location: "jaw",
    x: 50,
    y: 100,
  },
  pointB: {
    id: 17,
    location: "jaw",
    x: 350,
    y: 100,
  },
  pointC: {
    id: 9,
    location: "jaw",
    x: 200,
    y: 250,
  },
};

export { defaultCanvas1A, defaultCanvas1B };
