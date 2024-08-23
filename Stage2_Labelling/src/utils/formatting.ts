// Function to format the directory name if it follows the YYYYMMDD-HHmmss pattern
export const formatDateTime = (input: string): string => {
  const datePart = input.slice(0, 8);
  const timePart = input.slice(9);

  const year = datePart.slice(0, 4);
  const month = datePart.slice(4, 6);
  const day = datePart.slice(6, 8);

  const hours = timePart.slice(0, 2);
  const minutes = timePart.slice(2, 4);
  const seconds = timePart.slice(4, 6);

  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
};
