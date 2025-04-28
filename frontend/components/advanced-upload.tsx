"use client"

import type React from "react"

import { useState } from "react"
import { FileUp, X, File, FileText, FileImage, FileArchive } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Checkbox } from "@/components/ui/checkbox"

export function AdvancedUpload() {
  const [files, setFiles] = useState<File[]>([])
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [recordType, setRecordType] = useState("lab-results")
  const [provider, setProvider] = useState("")
  const [date, setDate] = useState("")
  const [autoAnalyze, setAutoAnalyze] = useState(true)

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
        return prev + 5
      })
    }, 300)
  }

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index))
  }

  const getFileIcon = (file: File) => {
    const extension = file.name.split(".").pop()?.toLowerCase()

    if (extension === "pdf") return <FileText className="h-4 w-4 text-red-500" />
    if (["jpg", "jpeg", "png", "gif"].includes(extension || "")) return <FileImage className="h-4 w-4 text-blue-500" />
    if (["zip", "rar", "dcm", "dicom"].includes(extension || ""))
      return <FileArchive className="h-4 w-4 text-amber-500" />

    return <File className="h-4 w-4 text-muted-foreground" />
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <label htmlFor="record-type" className="text-sm font-medium">
            Record Type
          </label>
          <select
            id="record-type"
            className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2"
            value={recordType}
            onChange={(e) => setRecordType(e.target.value)}
          >
            <option value="lab-results">Lab Results</option>
            <option value="imaging">Imaging (X-Ray, MRI, CT)</option>
            <option value="doctor-notes">Doctor Notes</option>
            <option value="prescription">Prescription</option>
            <option value="discharge">Discharge Summary</option>
            <option value="other">Other</option>
          </select>
        </div>
        <div>
          <label htmlFor="provider" className="text-sm font-medium">
            Healthcare Provider
          </label>
          <input
            id="provider"
            type="text"
            placeholder="e.g., Quest Diagnostics, City Hospital"
            className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2"
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
          />
        </div>
      </div>

      <div>
        <label htmlFor="record-date" className="text-sm font-medium">
          Record Date
        </label>
        <input
          id="record-date"
          type="date"
          className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2"
          value={date}
          onChange={(e) => setDate(e.target.value)}
        />
      </div>

      <div
        className="border-2 border-dashed rounded-lg p-6 text-center cursor-pointer hover:bg-slate-50 transition-colors"
        onClick={() => document.getElementById("advanced-file-upload")?.click()}
      >
        <FileUp className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
        <p className="text-sm font-medium mb-1">Drag and drop your files here</p>
        <p className="text-xs text-muted-foreground mb-2">Supports PDF, JPEG, PNG, DICOM, and EHR exports</p>
        <Button variant="secondary" size="sm">
          Browse Files
        </Button>
        <input id="advanced-file-upload" type="file" multiple className="hidden" onChange={handleFileChange} />
      </div>

      {files.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-medium">Selected Files:</p>
          {files.map((file, index) => (
            <div key={index} className="flex items-center justify-between bg-slate-50 p-2 rounded">
              <div className="flex items-center">
                {getFileIcon(file)}
                <span className="text-sm ml-2 truncate max-w-[200px]">{file.name}</span>
              </div>
              <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => removeFile(index)}>
                <X className="h-4 w-4" />
              </Button>
            </div>
          ))}

          <div className="flex items-center space-x-2 mt-4">
            <Checkbox
              id="auto-analyze"
              checked={autoAnalyze}
              onCheckedChange={(checked) => setAutoAnalyze(!!checked)}
            />
            <label
              htmlFor="auto-analyze"
              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
            >
              Automatically analyze after upload
            </label>
          </div>

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
