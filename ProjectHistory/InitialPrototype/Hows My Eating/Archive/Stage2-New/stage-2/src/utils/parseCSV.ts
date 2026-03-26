import Papa from 'papaparse';

export const parseCSV = (csvFile: string, callback: (data: any) => void): void => {
  Papa.parse(csvFile, {
    complete: (result: any) => {
      const data = result.data;
      callback(data);
    },
    header: true,
  });
};