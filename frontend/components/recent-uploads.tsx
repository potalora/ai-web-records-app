"use client"

import { useState, useEffect } from "react"
import { FileText, FileImage, FileArchive, AlertCircle } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import apiClient, { RecentUpload } from "@/lib/api-client"

export function RecentUploads() {
  const [uploads, setUploads] = useState<RecentUpload[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchRecentUploads = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await apiClient.getRecentUploads(4) // Limit to 4 for the dashboard
        setUploads(data)
      } catch (err: any) {
        console.error('Error fetching recent uploads:', err)
        setError(err.detail || 'Failed to load recent uploads')
      } finally {
        setLoading(false)
      }
    }

    fetchRecentUploads()
  }, [])

  const getFileIcon = (fileType: string) => {
    if (fileType.includes('pdf')) return <FileText className="h-5 w-5 mr-3 text-red-500" />
    if (fileType.includes('image') || fileType.includes('dicom')) return <FileImage className="h-5 w-5 mr-3 text-blue-500" />
    return <FileArchive className="h-5 w-5 mr-3 text-amber-500" />
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'COMPLETED': return 'bg-green-100 text-green-800'
      case 'PROCESSING': return 'bg-blue-100 text-blue-800'
      case 'PENDING': return 'bg-yellow-100 text-yellow-800'
      case 'FAILED': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffHours / 24)

    if (diffHours < 1) return 'Less than an hour ago'
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
    return date.toLocaleDateString()
  }

  if (loading) {
    return (
      <div className="space-y-2">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="flex items-center p-2">
            <Skeleton className="h-5 w-5 mr-3" />
            <div className="flex-1">
              <Skeleton className="h-4 w-32 mb-1" />
              <Skeleton className="h-3 w-20" />
            </div>
            <Skeleton className="h-5 w-16" />
          </div>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="space-y-4">
      {uploads.length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-4">
          No recent uploads found. Upload medical data to get started.
        </p>
      ) : (
        <div className="space-y-2">
          {uploads.map((upload) => (
            <div key={upload.id} className="flex items-center p-2 hover:bg-slate-50 rounded-md">
              {getFileIcon(upload.fileType)}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{upload.filename}</p>
                <p className="text-xs text-muted-foreground">{formatDate(upload.uploadedAt)}</p>
              </div>
              <div className="ml-2">
                <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${getStatusColor(upload.status)}`}>
                  {upload.status.charAt(0) + upload.status.slice(1).toLowerCase()}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
