import { useChewingDataContext } from "../context/ChewingDataContextProvider"
import { join } from "@tauri-apps/api/path"
import { readDir, readTextFile } from "@tauri-apps/plugin-fs"
import { useEffect, useState } from "react"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "./ui/accordion"
import { Button } from "./ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "./ui/dialog"
import { useAppContext } from "../context/AppContext"
import { isValidState } from "../utilities/isValid"

const ImportedData = () => {
  const { appConfig } = useAppContext()
  const { selectedData, selectedArchivedData, fileSystemUpdate } = useChewingDataContext()

  const [importedFolderName, setImportedFolderName] = useState<string>("")
  const [files, setFiles] = useState<{ name: string; path: string | null; content: string | null; readable: boolean }[]>([])
  const [hasErrors, setHasErrors] = useState<boolean>(false)

  useEffect(() => {
    if (!selectedData && !selectedArchivedData) return
    if (!isValidState(appConfig)) return

    const fetchData = async (selected: string) => {
      setHasErrors(false)

      try {
        const folderName = selected.split("/").pop() || ""
        setImportedFolderName(folderName)

        const directoryContents = await readDir(selected)

        const filePatterns = [
          { name: "Motion Data JSON", pattern: folderName, extension: ".json" },
          { name: "Original Video", pattern: folderName, extension: ".mov" },
          { name: "Mov Info", pattern: "mov_info", extension: ".json" },
          { name: "Points Data", pattern: "step1_points_data", extension: ".csv" },
          { name: "Processed Video", pattern: "step1_processed_video", extension: ".mp4" },
          { name: "Ratios Data", pattern: "step1_ratios", extension: ".csv" },
          { name: "Labelled Data", pattern: appConfig.labelledJsonStartsWithString, extension: ".json" },
          { name: "Merged Data", pattern: appConfig.mergedCsvFileName, extension: ".csv" },
          { name: "Verified Data", pattern: appConfig.verifiedJsonStartsWithString, extension: ".json" },
        ]

        const newFiles = await Promise.all(
          filePatterns.map(async ({ name, pattern, extension }) => {
            const file = directoryContents.find(
              (file) => file.name?.startsWith(pattern) && file.name?.endsWith(extension),
            )
            const path = file ? await join(selected, file.name) : null

            const readable = file ? extension === ".json" || extension === ".csv" || extension === ".md" : false
            return { name, path, content: null, readable }
          }),
        )

        setFiles(newFiles)
      } catch (error) {
        console.error("Error fetching selected data:", error)
        setHasErrors(true)
      }
    }

    if (selectedData) fetchData(selectedData)
    if (selectedArchivedData) fetchData(selectedArchivedData)
  }, [selectedData])

  useEffect(() => {
    console.log("fileSystemUpdate", fileSystemUpdate)
  }, [fileSystemUpdate])

  const handleShowContent = async (index: number) => {
    if (files[index].path && !files[index].content) {
      try {
        const content = await readTextFile(files[index].path!)
        const updatedFiles = [...files]
        updatedFiles[index].content = content
        setFiles(updatedFiles)
      } catch (error) {
        console.error("Error reading file content:", error)
      }
    }
  }

  return (
    <div className="w-full max-w-2xl mx-auto p-4">
      <Accordion type="single" collapsible className="w-full">
        <AccordionItem value="imported-data">
          <AccordionTrigger>Imported Data: {importedFolderName}</AccordionTrigger>
          <AccordionContent>
            {hasErrors && <p className="text-red-500">Error loading data</p>}
            {files.map((file, index) => (
              <div key={file.name} className="mb-2">
                <Dialog>
                  <DialogTrigger asChild>
                    <Button variant="link" className="p-0">
                      {file.name}: {file.path ? file.path.split("/").pop() : "Not found"}
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>{file.name}</DialogTitle>
                    </DialogHeader>
                    <div className="mt-2 overflow-y-auto flex-grow">
                      <p className="font-semibold">Full Path:</p>
                      <p className="text-sm break-all">{file.path || "Not found"}</p>
                      {file.path && file.readable && (
                        <div className="mt-4">
                          <Button onClick={() => handleShowContent(index)}>
                            {file.content ? "Hide Content" : "Show Content"}
                          </Button>
                          {file.content && (
                            <div className="mt-2 p-2 bg-gray-100 rounded overflow-auto max-h-[50vh]">
                              <pre className="text-xs whitespace-pre-wrap break-words">{file.content}</pre>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </DialogContent>
                </Dialog>
              </div>
            ))}
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </div>
  )
}

export default ImportedData

