"use client"

import type React from "react"

import { useState, useRef } from "react"
import { FileUp, File, X, FolderUp, AlertCircle, CheckCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Alert, AlertDescription } from "@/components/ui/alert"
import apiClient from "@/lib/api-client"
import { useFileUpload } from "@/hooks/use-api"

export function UploadCard() {
  const [files, setFiles] = useState<File[]>([])
  const [uploadType, setUploadType] = useState<'files' | 'directory'>('files')
  const [success, setSuccess] = useState<string | null>(null)

  const {
    upload,
    uploading,
    progress,
    error,
    result,
    reset
  } = useFileUpload(apiClient.ingestFiles)

  const MAX_FILES = 10000; // Increased limit significantly, was 1000

  const fileInputRef = useRef<HTMLInputElement>(null)
  const dirInputRef = useRef<HTMLInputElement>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files)
      // Check file count before setting state
      if (newFiles.length > MAX_FILES) {
        console.error(`Too many files. Maximum number of files is ${MAX_FILES}.`);
        setFiles([]); // Clear selection
        setUploadType('files'); // Reset type
        return;
      }
      
      reset(); // Clear previous errors and results
      setSuccess(null);
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
    if (files.length === 0) {
      return;
    }

    if (files.length > MAX_FILES) {
      console.error(`Too many files selected. Maximum is ${MAX_FILES}. Please reduce selection.`);
      return;
    }

    try {
      const uploadResult = await upload(files);
      setSuccess(`Successfully uploaded ${files.length} files. Batch ID: ${uploadResult.batch_id}`);
      setFiles([]);
      
      // Reset file inputs
      if (fileInputRef.current) fileInputRef.current.value = '';
      if (dirInputRef.current) dirInputRef.current.value = '';
      
    } catch (error) {
      console.error("Upload failed:", error);
      // Error is already handled by useFileUpload hook
    }
  }

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index))
  }

  return (
    <div className="space-y-4">
      {/* Success Message */}
      {success && (
        <Alert>
          <CheckCircle className="h-4 w-4" />
          <AlertDescription>{success}</AlertDescription>
        </Alert>
      )}

      {/* Error Message */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error.detail || 'Upload failed'}</AlertDescription>
        </Alert>
      )}

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

          {uploading ? (
            <div className="space-y-2">
              <Progress value={progress} />
              <p className="text-xs text-center text-muted-foreground">
                Uploading {files.length} files... {progress}%
              </p>
            </div>
          ) : (
            <Button onClick={handleUpload} className="w-full" disabled={uploading || files.length === 0}> 
              Upload {files.length} {files.length === 1 ? "Item" : "Items"} ({uploadType})
            </Button>
          )}
        </div>
      )}
    </div>
  )
}
