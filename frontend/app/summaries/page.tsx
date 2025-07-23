import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { FileText, Calendar, Download, Plus } from "lucide-react"
import { DashboardHeader } from "@/components/dashboard-header"
import { DashboardNav } from "@/components/dashboard-nav"
import Link from "next/link"

export default function SummariesPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <DashboardHeader />
      <div className="flex flex-1">
        <DashboardNav />
        <main className="flex-1 p-6">
          <div className="flex flex-col gap-6">
            <div className="flex items-center justify-between">
              <h1 className="text-3xl font-bold">Health Summaries</h1>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Generate Summary
              </Button>
            </div>

            {/* Summary Stats */}
            <div className="grid gap-4 md:grid-cols-3">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Summaries</CardTitle>
                  <FileText className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">5</div>
                  <p className="text-xs text-muted-foreground">+2 this month</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Records Analyzed</CardTitle>
                  <FileText className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">12</div>
                  <p className="text-xs text-muted-foreground">Across all summaries</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Last Generated</CardTitle>
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">3d</div>
                  <p className="text-xs text-muted-foreground">ago</p>
                </CardContent>
              </Card>
            </div>

            {/* Generated Summaries */}
            <Card>
              <CardHeader>
                <CardTitle>Generated Summaries</CardTitle>
                <CardDescription>AI-generated summaries of your health records</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <SummaryItem
                    title="Comprehensive Health Summary"
                    date="Apr 20, 2023"
                    description="Complete summary of all health records including recent lab results and clinical notes"
                    recordCount={8}
                    href="/summaries/1"
                  />
                  <SummaryItem
                    title="Lab Results Analysis"
                    date="Apr 16, 2023"
                    description="Detailed analysis of recent laboratory test results with trend analysis"
                    recordCount={3}
                    href="/summaries/2"
                  />
                  <SummaryItem
                    title="Annual Health Review"
                    date="Feb 15, 2023"
                    description="Summary of annual physical examination and related diagnostic tests"
                    recordCount={4}
                    href="/summaries/3"
                  />
                  <SummaryItem
                    title="Cardiovascular Health Summary"
                    date="Jan 20, 2023"
                    description="Focused summary of cardiovascular-related tests and assessments"
                    recordCount={2}
                    href="/summaries/4"
                  />
                </div>
              </CardContent>
            </Card>

            {/* Create Custom Summary */}
            <Card>
              <CardHeader>
                <CardTitle>Create Custom Summary</CardTitle>
                <CardDescription>Generate a summary from specific health records</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <label htmlFor="summary-title" className="text-sm font-medium">
                      Summary Title
                    </label>
                    <input
                      id="summary-title"
                      type="text"
                      placeholder="e.g., Quarterly Health Review"
                      className="w-full rounded-md border border-input bg-background px-3 py-2"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Select Records to Include</label>
                    <div className="space-y-2 max-h-40 overflow-y-auto">
                      <div className="flex items-center space-x-2">
                        <input type="checkbox" id="record-1" className="rounded border-gray-300" />
                        <label htmlFor="record-1" className="text-sm">
                          Complete Blood Count (Apr 15, 2023)
                        </label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <input type="checkbox" id="record-2" className="rounded border-gray-300" />
                        <label htmlFor="record-2" className="text-sm">
                          Chest X-Ray Report (Mar 22, 2023)
                        </label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <input type="checkbox" id="record-3" className="rounded border-gray-300" />
                        <label htmlFor="record-3" className="text-sm">
                          Annual Physical Exam (Feb 10, 2023)
                        </label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <input type="checkbox" id="record-4" className="rounded border-gray-300" />
                        <label htmlFor="record-4" className="text-sm">
                          Lipid Panel (Feb 10, 2023)
                        </label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <input type="checkbox" id="record-5" className="rounded border-gray-300" />
                        <label htmlFor="record-5" className="text-sm">
                          Allergy Test Results (Jan 5, 2023)
                        </label>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Summary Options</label>
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <input type="checkbox" id="include-trends" className="rounded border-gray-300" />
                        <label htmlFor="include-trends" className="text-sm">
                          Include health trends over time
                        </label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <input type="checkbox" id="include-recommendations" className="rounded border-gray-300" />
                        <label htmlFor="include-recommendations" className="text-sm">
                          Include health recommendations
                        </label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <input type="checkbox" id="detailed-analysis" className="rounded border-gray-300" />
                        <label htmlFor="detailed-analysis" className="text-sm">
                          Include detailed analysis
                        </label>
                      </div>
                    </div>
                  </div>

                  <div className="flex justify-end">
                    <Button>Generate Summary</Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    </div>
  )
}

function SummaryItem({
  title,
  date,
  description,
  recordCount,
  href,
}: {
  title: string
  date: string
  description: string
  recordCount: number
  href: string
}) {
  return (
    <div className="rounded-lg border p-4">
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <h3 className="font-medium">{title}</h3>
          <div className="flex items-center gap-2 mt-1">
            <div className="flex items-center text-xs text-muted-foreground">
              <Calendar className="h-3 w-3 mr-1" />
              {date}
            </div>
            <div className="text-xs text-muted-foreground">
              {recordCount} {recordCount === 1 ? "record" : "records"}
            </div>
          </div>
          <p className="text-sm text-muted-foreground mt-2">{description}</p>
        </div>
        <div className="flex gap-2 ml-4">
          <Link href={href}>
            <Button size="sm">View</Button>
          </Link>
          <Button size="sm" variant="outline">
            <Download className="h-4 w-4 mr-1" />
            Export
          </Button>
        </div>
      </div>
    </div>
  )
}
