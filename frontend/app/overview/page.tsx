"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { FileUp, FileText, BookOpen, TestTube, AlertCircle } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { DashboardHeader } from "@/components/dashboard-header"
import { DashboardNav } from "@/components/dashboard-nav"
import { UploadCard } from "@/components/upload-card"
import { RecentUploads } from "@/components/recent-uploads"
import { HealthSummary } from "@/components/health-summary"
import { ProtectedRoute } from "@/components/auth/protected-route"
import apiClient, { DashboardStats } from "@/lib/api-client"
import Link from "next/link"

export default function OverviewPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchDashboardStats = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await apiClient.getDashboardStats()
        setStats(data)
      } catch (err: any) {
        console.error('Error fetching dashboard stats:', err)
        setError(err.detail || 'Failed to load dashboard statistics')
      } finally {
        setLoading(false)
      }
    }

    fetchDashboardStats()
  }, [])

  const formatChange = (change: number) => {
    const prefix = change > 0 ? '+' : ''
    return `${prefix}${change} this month`
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
              <h1 className="text-3xl font-bold">Overview</h1>
              <Link href="/records/upload">
                <Button>
                  <FileUp className="mr-2 h-4 w-4" />
                  Upload Records
                </Button>
              </Link>
            </div>

            {/* Quick Stats */}
            <div className="grid gap-4 md:grid-cols-4">
              {loading ? (
                // Loading skeletons
                [...Array(4)].map((_, i) => (
                  <Card key={i}>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <Skeleton className="h-4 w-24" />
                      <Skeleton className="h-4 w-4" />
                    </CardHeader>
                    <CardContent>
                      <Skeleton className="h-8 w-12 mb-1" />
                      <Skeleton className="h-3 w-20" />
                    </CardContent>
                  </Card>
                ))
              ) : error ? (
                // Error state
                <div className="md:col-span-4">
                  <Alert>
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                </div>
              ) : stats ? (
                // Stats cards
                <>
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Total Records</CardTitle>
                      <FileText className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{stats.totalRecords}</div>
                      <p className="text-xs text-muted-foreground">{formatChange(stats.recentRecordsChange)}</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Evidence Searches</CardTitle>
                      <TestTube className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{stats.evidenceSearches}</div>
                      <p className="text-xs text-muted-foreground">{formatChange(stats.recentEvidenceChange)}</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Summaries</CardTitle>
                      <BookOpen className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{stats.summariesGenerated}</div>
                      <p className="text-xs text-muted-foreground">{formatChange(stats.recentSummariesChange)}</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">This Month</CardTitle>
                      <FileText className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">
                        {stats.recentRecordsChange + stats.recentSummariesChange}
                      </div>
                      <p className="text-xs text-muted-foreground">new activities</p>
                    </CardContent>
                  </Card>
                </>
              ) : null}
            </div>

            {/* Main Content Grid */}
            <div className="grid gap-6 md:grid-cols-2">
              {/* Health Summary */}
              <Card className="md:col-span-2">
                <CardHeader>
                  <CardTitle>Health Summary</CardTitle>
                  <CardDescription>AI-generated overview based on your medical records</CardDescription>
                </CardHeader>
                <CardContent>
                  <HealthSummary />
                </CardContent>
              </Card>

              {/* Recent Uploads */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle>Recent Records</CardTitle>
                    <CardDescription>Your recently uploaded medical data</CardDescription>
                  </div>
                  <Link href="/records">
                    <Button variant="outline" size="sm">
                      View All
                    </Button>
                  </Link>
                </CardHeader>
                <CardContent>
                  <RecentUploads />
                </CardContent>
              </Card>

              {/* Quick Upload */}
              <Card>
                <CardHeader>
                  <CardTitle>Quick Upload</CardTitle>
                  <CardDescription>Upload new medical records</CardDescription>
                </CardHeader>
                <CardContent>
                  <UploadCard />
                </CardContent>
              </Card>
            </div>

            {/* Quick Actions */}
            <div className="grid gap-4 md:grid-cols-3">
              <Card className="cursor-pointer hover:bg-slate-50 transition-colors">
                <Link href="/records">
                  <CardContent className="flex items-center p-6">
                    <FileText className="h-8 w-8 text-teal-600 mr-4" />
                    <div>
                      <h3 className="font-medium">Manage Records</h3>
                      <p className="text-sm text-muted-foreground">View and organize your health records</p>
                    </div>
                  </CardContent>
                </Link>
              </Card>

              <Card className="cursor-pointer hover:bg-slate-50 transition-colors">
                <Link href="/records/labs">
                  <CardContent className="flex items-center p-6">
                    <TestTube className="h-8 w-8 text-purple-600 mr-4" />
                    <div>
                      <h3 className="font-medium">Lab Results</h3>
                      <p className="text-sm text-muted-foreground">Review your test results and trends</p>
                    </div>
                  </CardContent>
                </Link>
              </Card>

              <Card className="cursor-pointer hover:bg-slate-50 transition-colors">
                <Link href="/summaries">
                  <CardContent className="flex items-center p-6">
                    <BookOpen className="h-8 w-8 text-blue-600 mr-4" />
                    <div>
                      <h3 className="font-medium">View Summaries</h3>
                      <p className="text-sm text-muted-foreground">Access AI-generated health summaries</p>
                    </div>
                  </CardContent>
                </Link>
              </Card>
            </div>
          </div>
        </main>
      </div>
    </div>
    </ProtectedRoute>
  )
}
