import React from 'react';

type TimelineProps = {
  played: number;
  duration: number;
  onSeekChange: (newPlayed: number) => void;
};

const Timeline: React.FC<TimelineProps> = ({ played, duration, onSeekChange }) => {
  return (
    <input
      type="range"
      min="0"
      max="1"
      step="0.01"
      value={played}
      onChange={(e) => onSeekChange(parseFloat(e.target.value))}
      className="w-full mx-2"
    />
  );
};

export default Timeline;
