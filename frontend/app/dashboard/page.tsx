'use client'

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { FileUp, FileText, Search, BookOpen } from "lucide-react"
import { DashboardHeader } from "@/components/dashboard-header"
import { DashboardNav } from "@/components/dashboard-nav"
import { UploadCard } from "@/components/upload-card"
import { RecentUploads } from "@/components/recent-uploads"
import { HealthSummary } from "@/components/health-summary"
import { MedicalRecordsTable } from "@/components/medical-records-table"
import { ProtectedRoute } from "@/components/auth/protected-route"
import apiClient, { DashboardStats } from "@/lib/api-client"
import { useApi } from "@/hooks/use-api"
import Link from "next/link"

export default function DashboardPage() {
  const {
    data: dashboardStats,
    loading: statsLoading,
    execute: fetchStats,
    error: statsError
  } = useApi(apiClient.getDashboardStats);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  return (
    <ProtectedRoute>
      <div className="flex min-h-screen flex-col">
        <DashboardHeader />
        <div className="flex flex-1">
          <DashboardNav />
          <main className="flex-1 p-6">
          <div className="flex flex-col gap-6">
            <div className="flex items-center justify-between">
              <h1 className="text-3xl font-bold">Dashboard</h1>
              <Link href="/dashboard/upload">
                <Button>
                  <FileUp className="mr-2 h-4 w-4" />
                  Upload Records
                </Button>
              </Link>
            </div>

            <Tabs defaultValue="overview" className="space-y-4">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="records">Records</TabsTrigger>
                <TabsTrigger value="evidence">Evidence</TabsTrigger>
              </TabsList>

              <TabsContent value="overview" className="space-y-4">
                <div className="grid gap-4 md:grid-cols-3">
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Total Records</CardTitle>
                      <FileText className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">
                        {statsLoading ? "..." : dashboardStats?.totalRecords || 0}
                      </div>
                      <p className="text-xs text-muted-foreground">
                        +{dashboardStats?.recentRecordsChange || 0} from last week
                      </p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Evidence Searches</CardTitle>
                      <Search className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">
                        {statsLoading ? "..." : dashboardStats?.evidenceSearches || 0}
                      </div>
                      <p className="text-xs text-muted-foreground">
                        +{dashboardStats?.recentEvidenceChange || 0} from last week
                      </p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Summaries Generated</CardTitle>
                      <BookOpen className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">
                        {statsLoading ? "..." : dashboardStats?.summariesGenerated || 0}
                      </div>
                      <p className="text-xs text-muted-foreground">
                        +{dashboardStats?.recentSummariesChange || 0} from last week
                      </p>
                    </CardContent>
                  </Card>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <Card className="col-span-1 md:col-span-2">
                    <CardHeader>
                      <CardTitle>Health Summary</CardTitle>
                      <CardDescription>AI-generated summary based on your medical records</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <HealthSummary />
                    </CardContent>
                  </Card>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <Card>
                    <CardHeader>
                      <CardTitle>Recent Uploads</CardTitle>
                      <CardDescription>Your recently uploaded medical data</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <RecentUploads />
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader>
                      <CardTitle>Quick Upload</CardTitle>
                      <CardDescription>Upload your medical data for AI analysis</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <UploadCard />
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>

              <TabsContent value="records" className="space-y-4">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between">
                    <div>
                      <CardTitle>Medical Records</CardTitle>
                      <CardDescription>View and manage all your uploaded medical records</CardDescription>
                    </div>
                    <Link href="/dashboard/upload">
                      <Button>
                        <FileUp className="mr-2 h-4 w-4" />
                        Upload New Record
                      </Button>
                    </Link>
                  </CardHeader>
                  <CardContent>
                    <MedicalRecordsTable />
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="evidence" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Medical Evidence Search</CardTitle>
                    <CardDescription>Search PubMed for authoritative medical evidence</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex gap-2">
                        <input
                          type="text"
                          placeholder="Search medical terms, conditions, or treatments..."
                          className="flex-1 rounded-md border border-input bg-background px-3 py-2"
                        />
                        <Button>Search</Button>
                      </div>

                      <div className="space-y-4">
                        <h3 className="text-lg font-medium">Recent Searches</h3>
                        <div className="space-y-3">
                          <EvidenceItem
                            title="Vitamin D Deficiency Treatment"
                            date="Apr 16, 2023"
                            results={12}
                            href="/dashboard/evidence/1"
                          />
                          <EvidenceItem
                            title="Hypertension Management"
                            date="Apr 10, 2023"
                            results={24}
                            href="/dashboard/evidence/2"
                          />
                          <EvidenceItem
                            title="Cholesterol Guidelines"
                            date="Mar 28, 2023"
                            results={18}
                            href="/dashboard/evidence/3"
                          />
                        </div>
                      </div>

                      <div className="space-y-4">
                        <h3 className="text-lg font-medium">Suggested Searches Based on Your Records</h3>
                        <div className="space-y-3">
                          <EvidenceItem
                            title="Latest Research on Vitamin D Supplementation"
                            date="Suggested"
                            results={null}
                            href="/dashboard/evidence/new?q=vitamin+d+supplementation"
                          />
                          <EvidenceItem
                            title="Blood Pressure Management Strategies"
                            date="Suggested"
                            results={null}
                            href="/dashboard/evidence/new?q=blood+pressure+management"
                          />
                        </div>
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

function EvidenceItem({
  title,
  date,
  results,
  href,
}: {
  title: string
  date: string
  results: number | null
  href: string
}) {
  return (
    <Link href={href} className="block rounded-lg border p-3 hover:bg-slate-50">
      <div className="flex justify-between items-start">
        <div>
          <h4 className="font-medium">{title}</h4>
          <p className="text-xs text-muted-foreground mt-1">
            {date} {results !== null && `• ${results} results`}
          </p>
        </div>
        <Button variant="ghost" size="sm">
          <Search className="h-4 w-4 mr-1" />
          {results === null ? "Search" : "View"}
        </Button>
      </div>
    </Link>
  )
}
