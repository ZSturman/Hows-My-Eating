
// import {
//   FaArrowDown,
//   FaArrowUp,
//   FaArrowLeft,
//   FaArrowRight,
// } from "react-icons/fa";
// import { MdOutlineKeyboardOptionKey } from "react-icons/md";
// import { PiCommand } from "react-icons/pi";
// import { useLabelContext } from "../context/LabellingContext";




// const LabelControls = () => {
//   const { state, dispatch } = useLabelContext();



//   return (
//     <div className="flex flex-col w-full max-w-[30%] p-6 space-y-6 bg-white rounded-md shadow-lg ml-4 border border-gray-200">
//       <div className="mb-4">
//         <h2 className="text-xl font-semibold mb-2">Current Labels</h2>
//         <div className="text-sm text-gray-700 space-y-2">
//           <p>
//             <span className="font-medium">Eating State:</span>{" "}
//             {state. ? "Eating" : "Not Eating"}
//           </p>
//           <p>
//             <span className="font-medium">Talking State:</span>{" "}
//             {frameLabels.isTalking ? "Talking" : "Not Talking"}
//           </p>
//           <p>
//             <span className="font-medium">Mouth State:</span> {frameLabels.mouthState}
//           </p>
//           <p>
//             <span className="font-medium">Primary Body State:</span>{" "}
//             {frameLabels.primaryBodyState}
//           </p>
//           <p>
//             <span className="font-medium">Mouth Action:</span>{" "}
//             {frameLabels.mouthAction || "None"}
//           </p>
//           <p>
//             <span className="font-medium">Body Action:</span>{" "}
//             {frameLabels.bodyAction || "None"}
//           </p>
//           {frameLabels.otherLabels.length > 0 && (
//             <p>
//               <span className="font-medium">Other Labels:</span>{" "}
//               {frameLabels.otherLabels.join(", ")}
//             </p>
//           )}
//         </div>
//       </div>

//       <div className="flex flex-row">
//         <div className="flex flex-col items-end justify-between">
//           <div className="border-2 border-solid border-black rounded-md p-1 flex flex-row items-center justify-center gap-2">
//             <PiCommand />
//             Home
//           </div>

//           <div
//             className={`border-2 border-solid border-black rounded-md p-1 flex flex-row items-center justify-center gap-2 ${
//               frameLabels.mouthState === "OPENING" ? "bg-green-500" : "bg-red-500"
//             }`}
//             onClick={() => handleLabelChange({ mouthState: "OPENING" })}
//           >
//             <FaArrowLeft />
//             <div>Opening</div>
//           </div>
//         </div>

//         <div className="flex flex-col justify-between gap-2 items-center mx-1">
//           <div
//             className={`border-2 border-solid border-black rounded-md p-1 flex flex-row items-center justify-center gap-2 ${
//               frameLabels.mouthState === "OPEN" ? "bg-green-500" : "bg-red-500"
//             }`}
//             onClick={() => handleLabelChange({ mouthState: "OPEN" })}
//           >
//             <FaArrowUp />
//             <div>Open</div>
//           </div>

//           <div
//             className={`border-2 border-solid border-black rounded-md p-1 flex flex-row items-center justify-center gap-2 ${
//               frameLabels.mouthState === "CLOSED" ? "bg-green-500" : "bg-red-500"
//             }`}
//             onClick={() => handleLabelChange({ mouthState: "CLOSED" })}
//           >
//             <FaArrowDown />
//             <div>Closed</div>
//           </div>
//         </div>

//         <div className="flex flex-col justify-between items-start">
//           <div className="border-2 border-solid border-black rounded-md p-1 flex flex-row items-center justify-center gap-2">
//             <MdOutlineKeyboardOptionKey />
//             Back
//           </div>
//           <div
//             className={`border-2 border-solid border-black rounded-md p-1 flex flex-row items-center justify-center gap-2 ${
//               frameLabels.mouthState === "CLOSING" ? "bg-green-500" : "bg-red-500"
//             }`}
//             onClick={() => handleLabelChange({ mouthState: "CLOSING" })}
//           >
//             <FaArrowRight />
//             <div>Closing</div>
//           </div>
//         </div>
//       </div>

//       <div className="mt-4">
//         <h3 className="text-lg font-semibold mb-2">Controls</h3>
//         <div className="flex flex-wrap gap-2">
//           <button
//             className="px-3 py-1 text-sm font-medium text-white bg-blue-500 rounded hover:bg-blue-600"
//             onClick={() => handleLabelChange({ isEating: !frameLabels.isEating })}
//           >
//             Toggle Eating State
//           </button>
//           <button
//             className="px-3 py-1 text-sm font-medium text-white bg-blue-500 rounded hover:bg-blue-600"
//             onClick={() => handleLabelChange({ isTalking: !frameLabels.isTalking })}
//           >
//             Toggle Talking State
//           </button>
//           <button
//             className="px-3 py-1 text-sm font-medium text-white bg-blue-500 rounded hover:bg-blue-600"
//             onClick={() =>
//               handleLabelChange({
//                 mouthState: frameLabels.mouthState === "CLOSED" ? "OPEN" : "CLOSED",
//               })
//             }
//           >
//             Toggle Mouth State
//           </button>
          
//         </div>
//       </div>
//     </div>
//   );
// };

// export default LabelControls;