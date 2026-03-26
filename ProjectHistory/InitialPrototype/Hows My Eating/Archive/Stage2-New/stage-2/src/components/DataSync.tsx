// // src/components/DataSync.tsx
// import React, { useState } from 'react';
// import { checkIfDataIsSynced, manuallySyncData } from '../utils/syncData';
// import { ProjectDataJson } from '../types';

// interface DataSyncProps {
//   projectData: ProjectDataJson;
//   onSyncComplete: () => void;
// }

// export const DataSync: React.FC<DataSyncProps> = ({ projectData, onSyncComplete }) => {
//   const [syncOffset, setSyncOffset] = useState<number | null>(null);
//   const [loading, setLoading] = useState(false);
//   const [manualSyncInProgress, setManualSyncInProgress] = useState(false);

//   // Function to check if data is synced
//   const handleSyncCheck = async () => {
//     setLoading(true);
//     const offset = await checkIfDataIsSynced(projectData.motionDataFilePath, projectData.movDataFilePath);
//     setSyncOffset(offset);
//     setLoading(false);
//   };

//   // Function to manually sync the data if offset is too large
//   const handleManualSync = async () => {
//     setManualSyncInProgress(true);
//     await manuallySyncData();
//     setManualSyncInProgress(false);
//     onSyncComplete();
//   };

//   return (
//     <div>
//       <h2>Step 2: Data Sync</h2>
//       <button onClick={handleSyncCheck} disabled={loading || manualSyncInProgress}>
//         {loading ? 'Checking Sync...' : 'Check Sync'}
//       </button>
//       {syncOffset !== null && (
//         <div>
//           {syncOffset <= 50 ? (
//             <p>Data is synced! Offset: {syncOffset}ms</p>
//           ) : (
//             <div>
//               <p>Data is not synced. Offset: {syncOffset}ms</p>
//               <button onClick={handleManualSync} disabled={manualSyncInProgress}>
//                 {manualSyncInProgress ? 'Syncing...' : 'Manually Sync Data'}
//               </button>
//             </div>
//           )}
//         </div>
//       )}
//     </div>
//   );
// };