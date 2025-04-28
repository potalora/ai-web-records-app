"use client"

import type React from "react"

import { useState, useRef } from "react"
import { FileUp, File, X, FolderUp } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"

export function UploadCard() {
  const [files, setFiles] = useState<File[]>([])
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [uploadType, setUploadType] = useState<'files' | 'directory'>('files')

  const MAX_FILES = 10000; // Increased limit significantly, was 1000

  const fileInputRef = useRef<HTMLInputElement>(null)
  const dirInputRef = useRef<HTMLInputElement>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files)
      // Check file count before setting state
      if (newFiles.length > MAX_FILES) {
        setError(`Too many files. Maximum number of files is ${MAX_FILES}.`);
        setFiles([]); // Clear selection
        setUploadType('files'); // Reset type
        return;
      }
      setError(null); // Clear previous errors
      setFiles(newFiles)
      setUploadType((newFiles[0] as any).webkitRelativePath ? 'directory' : 'files')
    }
  }

  const triggerFileInput = (type: 'files' | 'directory') => {
    setUploadType(type)
    if (type === 'files' && fileInputRef.current) {
        fileInputRef.current.click()
    } else if (type === 'directory' && dirInputRef.current) {
        dirInputRef.current.click()
    }
  }

  const handleUpload = async () => {
    // Double-check count before sending (though handleFileChange should prevent this state)
    if (files.length > MAX_FILES) {
        setError(`Too many files selected. Maximum is ${MAX_FILES}. Please reduce selection.`);
        return;
    }
    if (files.length === 0) {
      setError("Please select files to upload.")
      return
    }

    setError(null) // Clear errors before upload

    const formData = new FormData()
    files.forEach((file) => {
      formData.append("files", file, file.name)
      if (uploadType === 'directory' && (file as any).webkitRelativePath) {
         // NOTE: Sending relative paths might require backend adjustments
         // depending on how FastAPI/Starlette handle file uploads.
         // A common pattern is to send metadata alongside the file.
         // For simplicity now, we rely on backend potentially inferring or we adjust later.
      }
    })
    formData.append('upload_type', uploadType)

    setUploading(true)
    setProgress(0)

    try {
      const response = await fetch("http://localhost:8000/ingest/files", {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      console.log("Upload successful:", result)
      setFiles([])
    } catch (err: any) {
      console.error("Upload failed:", err)
      setError(err.message || "An unknown error occurred during upload.")
    } finally {
      setUploading(false)
      setProgress(0)
    }
  }

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index))
  }

  return (
    <div className="space-y-4">
      <div
        className="border-2 border-dashed rounded-lg p-6 text-center cursor-pointer hover:bg-slate-50 transition-colors"
        onClick={() => triggerFileInput('files')}
      >
        <FileUp className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
        <p className="text-sm font-medium mb-1">Drag & Drop Files or Click to Browse</p>
        <p className="text-xs text-muted-foreground mb-2">Supports PDF, JPEG, PNG, DICOM, TXT etc.</p>
        <input id="file-upload" type="file" multiple className="hidden" ref={fileInputRef} onChange={handleFileChange} />
      </div>

      <div
        className="border-2 border-dashed rounded-lg p-6 text-center cursor-pointer hover:bg-slate-50 transition-colors"
        onClick={() => triggerFileInput('directory')}
      >
        <FolderUp className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
        <p className="text-sm font-medium mb-1">Click to Upload EHR Directory</p>
        <p className="text-xs text-muted-foreground mb-2">Select the root folder containing TSV/HTM files</p>
        <input id="dir-upload" type="file" multiple className="hidden" ref={dirInputRef} onChange={handleFileChange} {...{ webkitdirectory: "true", mozdirectory: "true", directory: "true" }} />
      </div>

      {files.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-medium">Selected Files:</p>
          {files.map((file, index) => (
            <div key={index} className="flex items-center justify-between bg-slate-50 p-2 rounded">
              <div className="flex items-center">
                <File className="h-4 w-4 mr-2 text-muted-foreground" />
                <span className="text-sm truncate max-w-[200px]">{file.name}</span>
                {(uploadType === 'directory' && (file as any).webkitRelativePath) &&
                  <span className="text-xs text-muted-foreground ml-2 truncate max-w-[150px]" title={(file as any).webkitRelativePath}>{(file as any).webkitRelativePath}</span>
                }
              </div>
              <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => removeFile(index)} disabled={uploading}>
                <X className="h-4 w-4" />
              </Button>
            </div>
          ))}

          {error && error.startsWith("Too many files") && (
            <p className="text-sm text-red-600">{error}</p>
          )}

          {uploading ? (
            <div className="space-y-2">
              <Progress value={progress} />
              <p className="text-xs text-center text-muted-foreground">Uploading...</p>
            </div>
          ) : (
            <Button onClick={handleUpload} className="w-full" disabled={uploading}> 
              Upload {files.length} {files.length === 1 ? "Item" : "Items"} ({uploadType})
            </Button>
          )}
        </div>
      )}
    </div>
  )
}
