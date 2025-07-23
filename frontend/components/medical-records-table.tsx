'use client'

import { useEffect } from "react"
import Link from "next/link"
import { Loader2, FileText, Stethoscope, TestTube, Brain } from "lucide-react"
import apiClient from "@/lib/api-client"
import { useApi } from "@/hooks/use-api"

export function MedicalRecordsTable() {
  const {
    data: medicalRecords,
    loading,
    execute: fetchRecords,
    error
  } = useApi(apiClient.getMedicalRecords);

  useEffect(() => {
    fetchRecords(); // Get all records
  }, [fetchRecords]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getRecordTypeIcon = (recordType: string) => {
    switch (recordType) {
      case 'LAB_RESULT':
        return <TestTube className="h-4 w-4 text-blue-500" />;
      case 'CLINICAL_NOTE':
        return <Stethoscope className="h-4 w-4 text-green-500" />;
      case 'RADIOLOGY':
        return <Brain className="h-4 w-4 text-purple-500" />;
      default:
        return <FileText className="h-4 w-4 text-gray-500" />;
    }
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

  const formatRecordType = (recordType: string) => {
    return recordType.replace(/_/g, ' ').toLowerCase().replace(/^\w/, c => c.toUpperCase());
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin" />
        <span className="ml-2 text-sm text-muted-foreground">Loading medical records...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-sm text-red-500">
          Failed to load medical records: {error.detail}
        </p>
      </div>
    );
  }

  if (!medicalRecords || medicalRecords.length === 0) {
    return (
      <div className="text-center py-8">
        <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-2" />
        <p className="text-sm text-muted-foreground">
          No medical records found. Upload your first medical document to get started.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-md border">
      <div className="grid grid-cols-5 p-4 font-medium border-b bg-muted/50">
        <div>Name</div>
        <div>Type</div>
        <div>Date</div>
        <div>Files</div>
        <div>Status</div>
      </div>
      <div className="divide-y">
        {medicalRecords.map((record) => (
          <Link 
            key={record.id} 
            href={`/dashboard/records/${record.id}`} 
            className="grid grid-cols-5 p-4 hover:bg-slate-50 transition-colors"
          >
            <div className="flex items-center">
              {getRecordTypeIcon(record.recordType)}
              <span className="ml-2 font-medium truncate">{record.title}</span>
            </div>
            <div className="text-muted-foreground">
              {formatRecordType(record.recordType)}
            </div>
            <div className="text-muted-foreground">
              {formatDate(record.createdAt)}
            </div>
            <div className="text-muted-foreground">
              {record.fileCount} {record.fileCount === 1 ? 'file' : 'files'}
              {record.summaryAvailable && (
                <span className="ml-2 text-xs text-blue-600">• Summary available</span>
              )}
            </div>
            <div>
              <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${getStatusColor(record.status)}`}>
                {record.status === 'COMPLETED' ? 'Analyzed' : record.status}
              </span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}