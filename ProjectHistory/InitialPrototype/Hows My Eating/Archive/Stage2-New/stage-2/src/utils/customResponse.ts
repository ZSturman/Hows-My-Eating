import { AppLog } from '../context/AppLogContext';

const createSuccessResponse = <T>(data: T, message: string = "Operation completed successfully"): AppLog => ({
    status: 'SUCCESS',
    payload: data,
    timestamp: Date.now(),
    message: message
  });
  
  // Utility function to create an error response
  const createErrorResponse = (message: string): AppLog => ({
    status: 'ERROR',
    message,
    timestamp: Date.now(),
  });

  export {
    createSuccessResponse,
    createErrorResponse,
  };