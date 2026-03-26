// import React from 'react';
// import { useAppState } from '../context/AppStateContext';
// import { getSelectedDataRecord } from '../utils/selectors';

// export const DataRecordDetails: React.FC = () => {
//   const { state } = useAppState();
//   const selectedDataRecord = getSelectedDataRecord(state);

//   return (
//     <div>
//       <h2>Data Record Details</h2>
//       {selectedDataRecord ? (
//         <div>
//           <p>Data Directory: {selectedDataRecord.dataDirectory}</p>
//           <p>Export Status: {selectedDataRecord.exportStatus ? 'Exported' : 'Not Exported'}</p>
//           {/* More details... */}
//         </div>
//       ) : (
//         <p>No data record selected.</p>
//       )}
//     </div>
//   );
// };