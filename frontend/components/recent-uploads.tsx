'use client'

import { useEffect } from "react"
import { FileText, FileImage, FileArchive, Loader2 } from "lucide-react"
import apiClient from "@/lib/api-client"
import { useApi } from "@/hooks/use-api"

export function RecentUploads() {
  const {
    data: uploads,
    loading,
    execute: fetchUploads,
    error
  } = useApi(apiClient.getRecentUploads);

  useEffect(() => {
    fetchUploads(5); // Get last 5 uploads
  }, [fetchUploads]);

  const getFileIcon = (fileType: string) => {
    if (fileType.includes('pdf')) {
      return <FileText className="h-5 w-5 mr-3 text-red-500" />;
    } else if (fileType.includes('image')) {
      return <FileImage className="h-5 w-5 mr-3 text-blue-500" />;
    } else {
      return <FileArchive className="h-5 w-5 mr-3 text-amber-500" />;
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return "Just now";
    if (diffInHours < 24) return `${diffInHours} hours ago`;
    if (diffInHours < 168) return `${Math.floor(diffInHours / 24)} days ago`;
    return date.toLocaleDateString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return "bg-green-100 text-green-800"
      case 'PROCESSING':
        return "bg-blue-100 text-blue-800"
      case 'PENDING':
        return "bg-yellow-100 text-yellow-800"
      case 'FAILED':
        return "bg-red-100 text-red-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-4">
        <Loader2 className="h-6 w-6 animate-spin" />
        <span className="ml-2 text-sm text-muted-foreground">Loading recent uploads...</span>
      </div>
    );
  }

  if (error) {
    return (
      <p className="text-sm text-red-500 text-center py-4">
        Failed to load recent uploads: {error.detail}
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {!uploads || uploads.length === 0 ? (
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
                  {upload.status === 'COMPLETED' ? 'Analyzed' : upload.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
