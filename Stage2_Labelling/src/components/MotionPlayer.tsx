import React, { useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';

type MotionPlayerProps = {
  data: MotionData[];
  playing: boolean;
  played: number;
  onPlayPause: () => void;
  duration: number;
};

const MotionPlayer: React.FC<MotionPlayerProps> = ({ data, playing, played }) => {
  const currentIndex = Math.floor(played * data.length);

  // Prepare data for charting
  const chartData = data.map((entry, index) => ({
    time: index,
    pitch: entry.attitude.pitch,
    roll: entry.attitude.roll,
    yaw: entry.attitude.yaw,
    gravityX: entry.gravity.x,
    gravityY: entry.gravity.y,
    gravityZ: entry.gravity.z,
    userAccX: entry.userAcceleration.x,
    userAccY: entry.userAcceleration.y,
    userAccZ: entry.userAcceleration.z,
    rotRateX: entry.rotationRate.x,
    rotRateY: entry.rotationRate.y,
    rotRateZ: entry.rotationRate.z,
  }));

  useEffect(() => {
    if (playing) {
      // Logic to sync the motion data playback with the video
    }
  }, [playing, played]);

  return (
    <div>
      <h3>Motion Data Graphs</h3>

      {/* Attitude Graph */}
{/*       <h4>Attitude</h4>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis />
          <Tooltip />
          <Legend />
          <ReferenceLine x={currentIndex} stroke="red" />
          <Line type="monotone" dataKey="pitch" stroke="#8884d8" name="Pitch" />
          <Line type="monotone" dataKey="roll" stroke="#82ca9d" name="Roll" />
          <Line type="monotone" dataKey="yaw" stroke="#ffc658" name="Yaw" />
        </LineChart>
      </ResponsiveContainer> */}

      {/* Gravity Graph */}
{/*       <h4>Gravity</h4>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis />
          <Tooltip />
          <Legend />
          <ReferenceLine x={currentIndex} stroke="red" />
          <Line type="monotone" dataKey="gravityX" stroke="#ff7300" name="Gravity X" />
          <Line type="monotone" dataKey="gravityY" stroke="#387908" name="Gravity Y" />
          <Line type="monotone" dataKey="gravityZ" stroke="#00C49F" name="Gravity Z" />
        </LineChart>
      </ResponsiveContainer> */}

      {/* User Acceleration Graph */}
      <h4>User Acceleration</h4>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis />
          <Tooltip />
          <Legend />
          <ReferenceLine x={currentIndex} stroke="red" />
          <Line type="monotone" dataKey="userAccX" stroke="#FF8042" name="User Acceleration X" />
          <Line type="monotone" dataKey="userAccY" stroke="#0088FE" name="User Acceleration Y" />
          <Line type="monotone" dataKey="userAccZ" stroke="#00C49F" name="User Acceleration Z" />
        </LineChart>
      </ResponsiveContainer>

      {/* Rotation Rate Graph */}
      <h4>Rotation Rate</h4>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis />
          <Tooltip />
          <Legend />
          <ReferenceLine x={currentIndex} stroke="red" />
          <Line type="monotone" dataKey="rotRateX" stroke="#FFBB28" name="Rotation Rate X" />
          <Line type="monotone" dataKey="rotRateY" stroke="#FF8042" name="Rotation Rate Y" />
          <Line type="monotone" dataKey="rotRateZ" stroke="#0088FE" name="Rotation Rate Z" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default MotionPlayer;
