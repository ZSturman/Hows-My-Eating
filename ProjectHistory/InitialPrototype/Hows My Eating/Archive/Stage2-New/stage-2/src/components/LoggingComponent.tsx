// import { useAppState } from "../context/AppStateContext";

// const LoggingComponent: React.FC = () => {
//     const { state, dispatch } = useAppState();
  
//     const addLogMessage = () => {
//       const newLog: Logger = {
//         title: 'New Log Entry',
//         description: 'This is a new log entry.',
//         type: 'INFO',
//         timestamp: Date.now(),
//         forUi: true,
//       };
  
//       //dispatch({ type: 'LOG_MESSAGE', payload: newLog });
//     };
  
//     const clearLogs = () => {
//       //dispatch({ type: 'CLEAR_LOGS' });
//     };
  
//     return (
//       <div>
//         <h2>Log Messages</h2>
//         <ul>
//           {state.logger.map((log, index) => (
//             <li key={index}>
//               <strong>{log.title}:</strong> {log.description} ({new Date(log.timestamp).toLocaleString()})
//             </li>
//           ))}
//         </ul>
//       </div>
//     );
//   };

//   export default LoggingComponent;
  