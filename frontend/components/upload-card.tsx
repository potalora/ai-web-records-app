"use client"

import type React from "react"

import { useState } from "react"
import { FileUp, File, X, CheckCircle, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Alert, AlertDescription } from "@/components/ui/alert"
import apiClient from "@/lib/api-client"

export function UploadCard() {
  const [files, setFiles] = useState<File[]>([])
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [uploadResult, setUploadResult] = useState<{ success: boolean; message: string } | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFiles(Array.from(e.target.files))
      setUploadResult(null) // Clear previous results
    }
  }

  const handleUpload = async () => {
    if (files.length === 0) return

    setUploading(true)
    setProgress(0)
    setUploadResult(null)

    try {
      // Simulate progress during upload
      const progressInterval = setInterval(() => {
        setProgress((prev) => Math.min(prev + 20, 90))
      }, 200)

      // Actually upload files
      const result = await apiClient.ingestFiles(files)
      
      clearInterval(progressInterval)
      setProgress(100)
      
      setUploadResult({
        success: true,
        message: result.message || `Successfully uploaded ${files.length} files`
      })
      
      // Clear files after successful upload
      setTimeout(() => {
        setFiles([])
        setProgress(0)
        setUploadResult(null)
      }, 3000)

    } catch (error: any) {
      setProgress(0)
      setUploadResult({
        success: false,
        message: error.detail || 'Failed to upload files'
      })
    } finally {
      setUploading(false)
    }
  }

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index))
    setUploadResult(null)
  }

  const isValidFileType = (file: File) => {
    const validTypes = [
      'application/pdf',
      'application/json',
      'application/xml',
      'text/xml',
      'text/plain',
      'image/jpeg',
      'image/png',
      'image/dicom'
    ]
    return validTypes.includes(file.type) || file.name.toLowerCase().endsWith('.dcm')
  }

  return (
    <div className="space-y-4">
      <div
        className="border-2 border-dashed rounded-lg p-6 text-center cursor-pointer hover:bg-slate-50 transition-colors"
        onClick={() => document.getElementById("file-upload")?.click()}
      >
        <FileUp className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
        <p className="text-sm font-medium mb-1">Drag and drop your files here</p>
        <p className="text-xs text-muted-foreground mb-2">Supports PDF, JSON, XML, TXT, JPEG, PNG, and DICOM files</p>
        <Button variant="secondary" size="sm">
          Browse Files
        </Button>
        <input 
          id="file-upload" 
          type="file" 
          multiple 
          className="hidden" 
          onChange={handleFileChange}
          accept=".pdf,.json,.xml,.txt,.jpg,.jpeg,.png,.dcm"
        />
      </div>

      {uploadResult && (
        <Alert className={uploadResult.success ? "border-green-200 bg-green-50" : "border-red-200 bg-red-50"}>
          {uploadResult.success ? (
            <CheckCircle className="h-4 w-4 text-green-600" />
          ) : (
            <AlertCircle className="h-4 w-4 text-red-600" />
          )}
          <AlertDescription className={uploadResult.success ? "text-green-800" : "text-red-800"}>
            {uploadResult.message}
          </AlertDescription>
        </Alert>
      )}

      {files.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-medium">Selected Files:</p>
          {files.map((file, index) => (
            <div key={index} className="flex items-center justify-between bg-slate-50 p-2 rounded">
              <div className="flex items-center">
                <File className="h-4 w-4 mr-2 text-muted-foreground" />
                <div className="flex flex-col min-w-0">
                  <span className="text-sm truncate max-w-[180px]">{file.name}</span>
                  <span className="text-xs text-muted-foreground">
                    {(file.size / 1024 / 1024).toFixed(1)} MB
                    {!isValidFileType(file) && (
                      <span className="text-amber-600 ml-1">(unsupported type)</span>
                    )}
                  </span>
                </div>
              </div>
              <Button 
                variant="ghost" 
                size="icon" 
                className="h-6 w-6" 
                onClick={() => removeFile(index)}
                disabled={uploading}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          ))}

          {uploading ? (
            <div className="space-y-2">
              <Progress value={progress} />
              <p className="text-xs text-center text-muted-foreground">
                Uploading... {progress}%
              </p>
            </div>
          ) : (
            <Button 
              onClick={handleUpload} 
              className="w-full"
              disabled={files.length === 0 || files.some(f => !isValidFileType(f))}
            >
              Upload {files.length} {files.length === 1 ? "File" : "Files"}
            </Button>
          )}
        </div>
      )}
    </div>
  )
}
