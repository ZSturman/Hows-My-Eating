// import  { useEffect } from 'react';
// import { useLabelContext } from '../context/LabellingContext';

// const LabelSyncComponent: React.FC = () => {
//   // Access the state and dispatch from the LabelContext
//   const { state, dispatch } = useLabelContext();

//   // Effect to synchronize the labels based on the current timestamp
//   useEffect(() => {
//     // Check if there are any labels in the labelHistory
//     if (state.labelHistory.length > 0) {
//       // Find the label closest to the current timestamp
//       const closestLabel = state.labelHistory.reduce((prev, curr) => {
//         return Math.abs(curr.timestamp - state.currentTimestamp) <
//           Math.abs(prev.timestamp - state.currentTimestamp)
//           ? curr
//           : prev;
//       });

//       // If the closest label is different from the current one, update the state
//       if (closestLabel.timestamp !== state.lastSetLabels.timestamp) {
//         dispatch({ type: 'ADD_LABEL', label: closestLabel });
//       }
//     }
//   }, [state.currentTimestamp, state.labelHistory, dispatch]); // Re-run effect when currentTimestamp or labelHistory changes

//   // Render the component that displays the labels
//   return (
//     <div>
//       <h2>Current Labels</h2>
//       <p>
//         Mouth State: {state.lastSetLabels.mouthState}
//         <br />
//         Is Talking: {state.lastSetLabels.isTalking ? 'Yes' : 'No'}
//         <br />
//         Is Eating: {state.lastSetLabels.isEating ? 'Yes' : 'No'}
//         <br />
//         Mouth Action: {state.lastSetLabels.mouthAction}
//         <br />
//         Body Action: {state.lastSetLabels.bodyAction}
//         <br />
//         Timestamp: {state.lastSetLabels.timestamp}
//       </p>
//     </div>
//   );
// };

// export default LabelSyncComponent;