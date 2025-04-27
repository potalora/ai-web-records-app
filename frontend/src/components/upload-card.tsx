"use client"

import type React from "react"

import { useState } from "react"
import { FileUp, File, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"

export function UploadCard() {
  const [files, setFiles] = useState<File[]>([])
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFiles(Array.from(e.target.files))
    }
  }

  const handleUpload = () => {
    if (files.length === 0) return

    setUploading(true)
    setProgress(0)

    // Simulate upload progress
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval)
          setUploading(false)
          return 100
        }
        return prev + 10
      })
    }, 500)
  }

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index))
  }

  return (
    <div className="space-y-4">
      <div
        className="border-2 border-dashed rounded-lg p-6 text-center cursor-pointer hover:bg-slate-50 transition-colors"
        onClick={() => document.getElementById("file-upload")?.click()}
      >
        <FileUp className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
        <p className="text-sm font-medium mb-1">Drag and drop your files here</p>
        <p className="text-xs text-muted-foreground mb-2">Supports PDF, JPEG, PNG, DICOM, and EHR exports</p>
        <Button variant="secondary" size="sm">
          Browse Files
        </Button>
        <input id="file-upload" type="file" multiple className="hidden" onChange={handleFileChange} />
      </div>

      {files.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-medium">Selected Files:</p>
          {files.map((file, index) => (
            <div key={index} className="flex items-center justify-between bg-slate-50 p-2 rounded">
              <div className="flex items-center">
                <File className="h-4 w-4 mr-2 text-muted-foreground" />
                <span className="text-sm truncate max-w-[200px]">{file.name}</span>
              </div>
              <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => removeFile(index)}>
                <X className="h-4 w-4" />
              </Button>
            </div>
          ))}

          {uploading ? (
            <div className="space-y-2">
              <Progress value={progress} />
              <p className="text-xs text-center text-muted-foreground">Uploading... {progress}%</p>
            </div>
          ) : (
            <Button onClick={handleUpload} className="w-full">
              Upload {files.length} {files.length === 1 ? "File" : "Files"}
            </Button>
          )}
        </div>
      )}
    </div>
  )
}
