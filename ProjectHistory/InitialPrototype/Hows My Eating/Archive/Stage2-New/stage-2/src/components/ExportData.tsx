// // src/components/ExportData.tsx
// import React, { useState } from 'react';
// import { checkThatLabelsHaveBeenAdded, saveTheCSVFileSomewhere } from '../utils/exportData';

// export const ExportData: React.FC = () => {
//   const [exporting, setExporting] = useState(false);
//   const [exportStatus, setExportStatus] = useState<string | null>(null);

//   const handleExport = async () => {
//     setExporting(true);
//     const labelsAdded = await checkThatLabelsHaveBeenAdded();
    
//     if (labelsAdded) {
//       await saveTheCSVFileSomewhere();
//       setExportStatus('Data exported successfully!');
//     } else {
//       setExportStatus('No labels have been added yet. Cannot export data.');
//     }
    
//     setExporting(false);
//   };

//   return (
//     <div>
//       <h2>Step 4: Export Data</h2>
//       <button onClick={handleExport} disabled={exporting}>
//         {exporting ? 'Exporting...' : 'Export Data'}
//       </button>
//       {exportStatus && <p>{exportStatus}</p>}
//     </div>
//   );
// };