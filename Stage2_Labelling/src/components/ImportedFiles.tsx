type ImportedFilesProps = {
    importedFiles: string[];
    
};

const ImportedFiles: React.FC<ImportedFilesProps> = ({ importedFiles }) => {
    return (
        <div className="flex flex-col items-center justify-center py-4 pr-2">
            <h1 className="text-2xl font-bold">Imported Files</h1>
            <ul className="list-disc list-inside">
                {importedFiles.map((file, index) => (
                    <li key={index}>{file}</li>
                ))}
            </ul>
        </div>
    );
}

export default ImportedFiles