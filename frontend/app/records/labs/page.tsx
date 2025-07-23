import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ArrowLeft, TestTube, TrendingUp, AlertCircle } from "lucide-react"
import { DashboardHeader } from "@/components/dashboard-header"
import { DashboardNav } from "@/components/dashboard-nav"
import Link from "next/link"

export default function LabResultsPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <DashboardHeader />
      <div className="flex flex-1">
        <DashboardNav />
        <main className="flex-1 p-6">
          <div className="flex flex-col gap-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Link href="/records">
                  <Button variant="ghost" size="icon">
                    <ArrowLeft className="h-5 w-5" />
                  </Button>
                </Link>
                <h1 className="text-2xl font-bold">Lab Results</h1>
              </div>
            </div>

            {/* Key Metrics */}
            <div className="grid gap-4 md:grid-cols-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Tests</CardTitle>
                  <TestTube className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">24</div>
                  <p className="text-xs text-muted-foreground">Across 5 lab visits</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Normal Results</CardTitle>
                  <TrendingUp className="h-4 w-4 text-green-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">19</div>
                  <p className="text-xs text-muted-foreground">79% of tests</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Abnormal Results</CardTitle>
                  <AlertCircle className="h-4 w-4 text-yellow-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">5</div>
                  <p className="text-xs text-muted-foreground">21% of tests</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Last Test</CardTitle>
                  <TestTube className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">15d</div>
                  <p className="text-xs text-muted-foreground">ago</p>
                </CardContent>
              </Card>
            </div>

            {/* Recent Lab Results */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Lab Results</CardTitle>
                <CardDescription>Your latest laboratory test results</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <LabResultItem
                    testName="Complete Blood Count"
                    date="Apr 15, 2023"
                    provider="Quest Diagnostics"
                    abnormalCount={1}
                    totalCount={8}
                    href="/records/1"
                  />
                  <LabResultItem
                    testName="Lipid Panel"
                    date="Feb 10, 2023"
                    provider="Quest Diagnostics"
                    abnormalCount={0}
                    totalCount={4}
                    href="/records/4"
                  />
                  <LabResultItem
                    testName="Allergy Test Results"
                    date="Jan 5, 2023"
                    provider="Allergy Specialists"
                    abnormalCount={3}
                    totalCount={12}
                    href="/records/5"
                  />
                </div>
              </CardContent>
            </Card>

            {/* Key Health Indicators */}
            <Card>
              <CardHeader>
                <CardTitle>Key Health Indicators</CardTitle>
                <CardDescription>Trending values from your lab results</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <HealthIndicator
                    name="Vitamin D"
                    currentValue="24 ng/mL"
                    status="Low"
                    trend="↓"
                    normalRange="30-100 ng/mL"
                  />
                  <HealthIndicator
                    name="Total Cholesterol"
                    currentValue="175 mg/dL"
                    status="Normal"
                    trend="↓"
                    normalRange="<200 mg/dL"
                  />
                  <HealthIndicator
                    name="Hemoglobin A1C"
                    currentValue="5.4%"
                    status="Normal"
                    trend="→"
                    normalRange="<5.7%"
                  />
                  <HealthIndicator
                    name="White Blood Cells"
                    currentValue="7.5 x10³/μL"
                    status="Normal"
                    trend="↑"
                    normalRange="4.5-11.0 x10³/μL"
                  />
                </div>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    </div>
  )
}

function LabResultItem({
  testName,
  date,
  provider,
  abnormalCount,
  totalCount,
  href,
}: {
  testName: string
  date: string
  provider: string
  abnormalCount: number
  totalCount: number
  href: string
}) {
  return (
    <Link href={href} className="block rounded-lg border p-4 hover:bg-slate-50">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="font-medium">{testName}</h3>
          <p className="text-sm text-muted-foreground">
            {provider} • {date}
          </p>
          <div className="mt-2 flex items-center gap-4">
            <span className="text-sm">
              {totalCount - abnormalCount} normal, {abnormalCount} abnormal
            </span>
            {abnormalCount > 0 && (
              <span className="inline-flex items-center rounded-full bg-yellow-100 px-2.5 py-0.5 text-xs font-medium text-yellow-800">
                Needs Attention
              </span>
            )}
          </div>
        </div>
        <Button variant="outline" size="sm">
          View Details
        </Button>
      </div>
    </Link>
  )
}

function HealthIndicator({
  name,
  currentValue,
  status,
  trend,
  normalRange,
}: {
  name: string
  currentValue: string
  status: string
  trend: string
  normalRange: string
}) {
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "normal":
        return "text-green-600 bg-green-100"
      case "low":
      case "high":
        return "text-yellow-600 bg-yellow-100"
      case "critical":
        return "text-red-600 bg-red-100"
      default:
        return "text-gray-600 bg-gray-100"
    }
  }

  return (
    <div className="flex justify-between items-center p-3 rounded-md border">
      <div>
        <h4 className="font-medium">{name}</h4>
        <p className="text-sm text-muted-foreground">Normal: {normalRange}</p>
      </div>
      <div className="text-right">
        <div className="flex items-center gap-2">
          <span className="font-bold">{currentValue}</span>
          <span className="text-lg">{trend}</span>
          <span
            className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${getStatusColor(status)}`}
          >
            {status}
          </span>
        </div>
      </div>
    </div>
  )
}
