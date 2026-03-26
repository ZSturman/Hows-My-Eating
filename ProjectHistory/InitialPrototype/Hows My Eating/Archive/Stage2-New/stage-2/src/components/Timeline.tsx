// const LabelledTimeline = ({
//   labelHistory,
//   currentFrame,
//   totalFrames,
// }: {
//   labelHistory: Labels[];
//   currentFrame: number;
//   totalFrames: number;
// }) => {
//   return (
//     <div className="relative flex flex-row justify-center items-center h-20 w-full">
//       {/* Timeline labels */}
//       {labelHistory.map((label, index) => (
//         <div key={index} className="w-full h-full">
//           <TimelineLabel label={label} index={index} totalFrames={totalFrames} />
//         </div>
//       ))}
//       {/* Playback marker */}
//       <PlaybackMarker currentFrame={currentFrame} totalFrames={totalFrames} />
//     </div>
//   );
// };

// export default LabelledTimeline;

// const PlaybackMarker = ({
//   currentFrame,
//   totalFrames,
// }: {
//   currentFrame: number;
//   totalFrames: number;
// }) => {
//   // Calculate the left position based on the current frame
//   const leftPercentage = (currentFrame / totalFrames) * 100;

//   return (
//     <div
//       className="absolute top-0 h-full w-1 bg-orange-500"
//       style={{ left: `${leftPercentage}%` }}
//     />
//   );
// };

// const TimelineLabel = ({
//   label,
//   index,
//   totalFrames,
// }: {
//   label: Labels;
//   index: number;
//   totalFrames: number;
// }) => {
//   // Calculate the left position of each label based on its timestamp
//   const leftPercentage = (label.startTime / totalFrames) * 100;

//   return (
//     <div
//       className="relative h-full w-full"
//       style={{ left: `${leftPercentage}%` }}
//     >
//       <div
//         className={`absolute h-full w-full ${
//           label.isEating ? "bg-green-500" : "bg-red-500"
//         }`}
//       />
//     </div>
//   );
// };