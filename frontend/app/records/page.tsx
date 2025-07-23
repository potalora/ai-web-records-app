"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { FileUp, TestTube, AlertCircle } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { DashboardHeader } from "@/components/dashboard-header"
import { DashboardNav } from "@/components/dashboard-nav"
import { ProtectedRoute } from "@/components/auth/protected-route"
import apiClient, { MedicalRecord } from "@/lib/api-client"
import Link from "next/link"

export default function RecordsPage() {
  const [records, setRecords] = useState<MedicalRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchRecords = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await apiClient.getMedicalRecords()
        setRecords(data)
      } catch (err: any) {
        console.error('Error fetching medical records:', err)
        setError(err.detail || 'Failed to load medical records')
      } finally {
        setLoading(false)
      }
    }

    fetchRecords()
  }, [])

  const filterRecordsByType = (type: string) => {
    switch (type) {
      case 'lab':
        return records.filter(r => r.recordType === 'LAB_RESULT')
      case 'imaging':
        return records.filter(r => r.recordType === 'RADIOLOGY')
      case 'clinical':
        return records.filter(r => r.recordType === 'CLINICAL_NOTE')
      default:
        return records
    }
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
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }
  return (
    <ProtectedRoute>
      <div className="flex min-h-screen flex-col">
        <DashboardHeader />
        <div className="flex flex-1">
          <DashboardNav />
          <main className="flex-1 p-6">
          <div className="flex flex-col gap-6">
            <div className="flex items-center justify-between">
              <h1 className="text-3xl font-bold">Medical Records</h1>
              <div className="flex gap-2">
                <Link href="/records/labs">
                  <Button variant="outline">
                    <TestTube className="mr-2 h-4 w-4" />
                    Lab Results
                  </Button>
                </Link>
                <Link href="/records/upload">
                  <Button>
                    <FileUp className="mr-2 h-4 w-4" />
                    Upload Records
                  </Button>
                </Link>
              </div>
            </div>

            <Tabs defaultValue="all" className="space-y-4">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="all">All Records</TabsTrigger>
                <TabsTrigger value="lab">Lab Results</TabsTrigger>
                <TabsTrigger value="imaging">Imaging</TabsTrigger>
                <TabsTrigger value="clinical">Clinical Notes</TabsTrigger>
              </TabsList>

              <TabsContent value="all" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>All Medical Records</CardTitle>
                    <CardDescription>Complete list of your uploaded medical records</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {loading ? (
                      <div className="space-y-2">
                        {[...Array(5)].map((_, i) => (
                          <div key={i} className="grid grid-cols-5 p-4">
                            <Skeleton className="h-4 w-24" />
                            <Skeleton className="h-4 w-16" />
                            <Skeleton className="h-4 w-20" />
                            <Skeleton className="h-4 w-28" />
                            <Skeleton className="h-4 w-16" />
                          </div>
                        ))}
                      </div>
                    ) : error ? (
                      <Alert>
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>{error}</AlertDescription>
                      </Alert>
                    ) : (
                      <div className="rounded-md border">
                        <div className="grid grid-cols-5 p-4 font-medium">
                          <div>Name</div>
                          <div>Type</div>
                          <div>Date</div>
                          <div>Files</div>
                          <div>Status</div>
                        </div>
                        <div className="divide-y">
                          {filterRecordsByType('all').length === 0 ? (
                            <div className="p-8 text-center text-muted-foreground">
                              No medical records found. Upload files to get started.
                            </div>
                          ) : (
                            filterRecordsByType('all').map((record) => (
                              <RecordRow
                                key={record.id}
                                name={record.title}
                                type={record.recordType.replace('_', ' ')}
                                date={formatDate(record.createdAt)}
                                provider={`${record.fileCount} files`}
                                status={record.status}
                                href={`/records/${record.id}`}
                                statusColor={getStatusColor(record.status)}
                              />
                            ))
                          )}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="lab" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Laboratory Results</CardTitle>
                    <CardDescription>Your lab test results and blood work</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="rounded-md border">
                      <div className="grid grid-cols-5 p-4 font-medium">
                        <div>Test Name</div>
                        <div>Type</div>
                        <div>Date</div>
                        <div>Provider</div>
                        <div>Status</div>
                      </div>
                      <div className="divide-y">
                        <RecordRow
                          name="Complete Blood Count"
                          type="CBC"
                          date="Apr 15, 2023"
                          provider="Quest Diagnostics"
                          status="Analyzed"
                          href="/records/1"
                        />
                        <RecordRow
                          name="Lipid Panel"
                          type="Cholesterol"
                          date="Feb 10, 2023"
                          provider="Quest Diagnostics"
                          status="Analyzed"
                          href="/records/4"
                        />
                        <RecordRow
                          name="Allergy Test Results"
                          type="Allergy Panel"
                          date="Jan 5, 2023"
                          provider="Allergy Specialists"
                          status="Analyzed"
                          href="/records/5"
                        />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="imaging" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Medical Imaging</CardTitle>
                    <CardDescription>X-rays, MRIs, CT scans, and other imaging studies</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="rounded-md border">
                      <div className="grid grid-cols-5 p-4 font-medium">
                        <div>Study Name</div>
                        <div>Type</div>
                        <div>Date</div>
                        <div>Provider</div>
                        <div>Status</div>
                      </div>
                      <div className="divide-y">
                        <RecordRow
                          name="Chest X-Ray Report"
                          type="X-Ray"
                          date="Mar 22, 2023"
                          provider="City Hospital"
                          status="Analyzed"
                          href="/records/2"
                        />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="clinical" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Clinical Notes</CardTitle>
                    <CardDescription>Doctor visits, consultations, and clinical documentation</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="rounded-md border">
                      <div className="grid grid-cols-5 p-4 font-medium">
                        <div>Visit Type</div>
                        <div>Specialty</div>
                        <div>Date</div>
                        <div>Provider</div>
                        <div>Status</div>
                      </div>
                      <div className="divide-y">
                        <RecordRow
                          name="Annual Physical Exam"
                          type="Primary Care"
                          date="Feb 10, 2023"
                          provider="Dr. Sarah Johnson"
                          status="Analyzed"
                          href="/records/3"
                        />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        </main>
      </div>
    </div>
    </ProtectedRoute>
  )
}

function RecordRow({
  name,
  type,
  date,
  provider,
  status,
  href,
  statusColor,
}: {
  name: string
  type: string
  date: string
  provider: string
  status: string
  href: string
  statusColor?: string
}) {
  return (
    <Link href={href} className="grid grid-cols-5 p-4 hover:bg-slate-50">
      <div className="font-medium">{name}</div>
      <div className="text-muted-foreground">{type}</div>
      <div className="text-muted-foreground">{date}</div>
      <div className="text-muted-foreground">{provider}</div>
      <div>
        <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColor || 'bg-green-100 text-green-800'}`}>
          {status.charAt(0) + status.slice(1).toLowerCase()}
        </span>
      </div>
    </Link>
  )
}
