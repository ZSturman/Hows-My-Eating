import React, { useState, useEffect } from 'react';
import { readDir, BaseDirectory, removeDir } from '@tauri-apps/api/fs';
import { formatDateTime } from '../utils/formatting';

type ImportedDataDirectoriesProps = {
    setSelectedDataPath: React.Dispatch<React.SetStateAction<string | null>>;
};

const ImportedDataDirectories: React.FC<ImportedDataDirectoriesProps> = ({ setSelectedDataPath }) => {
    const [importedDirectories, setImportedDirectories] = useState<{ path: string, displayName: string }[]>([]);
    const [directoryContents, setDirectoryContents] = useState<{ [key: string]: string[] }>({});

    useEffect(() => {
        const fetchImportedDirectories = async () => {
            try {
                const appDataDirectories = await readDir('RecordedData', { dir: BaseDirectory.AppData });

                const directories = appDataDirectories
                    .filter(entry => entry.children)
                    .map(entry => {
                        const name = entry.name ? entry.name : entry.path.split('/').pop() || '';
                        const displayName = /^\d{8}-\d{6}$/.test(name) ? formatDateTime(name) : name;
                        return { path: entry.path, displayName };
                    });

                setImportedDirectories(directories);
                if (directories.length > 0) {
                    setSelectedDataPath(directories[0].path);
                    fetchDirectoryContents(directories[0].path);
                }
            } catch (error) {
                console.error('Error reading imported directories:', error);
            }
        };

        fetchImportedDirectories();
    }, []);

    const fetchDirectoryContents = async (dirPath: string) => {
        try {
            const contents = await readDir(dirPath, { dir: BaseDirectory.AppData });

            const contentNames = contents.map(item => item.name || item.path.split('/').pop() || '');
            setDirectoryContents(prev => ({ ...prev, [dirPath]: contentNames }));
        } catch (error) {
            console.error('Error reading directory contents:', error);
        }
    };

    const removeDirectory = async (dirPath: string) => {
        try {
            await removeDir(dirPath, { dir: BaseDirectory.AppData, recursive: true });
            setImportedDirectories(prevDirectories => prevDirectories.filter(directory => directory.path !== dirPath));
            setDirectoryContents(prevContents => {
                const updatedContents = { ...prevContents };
                delete updatedContents[dirPath];
                return updatedContents;
            });
        } catch (error) {
            console.error('Error deleting directory:', error);
        }
    };

    const handleNewSelection = (dirPath: string) => {
        setSelectedDataPath(dirPath);
        fetchDirectoryContents(dirPath);
    };

    return (
        <div className="flex flex-col items-center justify-center py-4 pr-2">
            <div className="flex flex-col">
                {importedDirectories.map((dir, index) => (
                    <div key={index} className="flex flex-col mb-4">
                        <div className="flex items-center">
                            <button onClick={() => removeDirectory(dir.path)} className="mr-2">
                                D
                            </button>
                            <button onClick={() => handleNewSelection(dir.path)}>
                                {dir.displayName}
                            </button>
                        </div>
                        {directoryContents[dir.path] && (
                            <div className="ml-4 mt-2">
                                <strong>Contents:</strong>
                                <ul className="list-disc list-inside">
                                    {directoryContents[dir.path].map((content, i) => (
                                        <li key={i}>{content}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};

export default ImportedDataDirectories;