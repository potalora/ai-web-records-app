import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ArrowLeft, Search, ExternalLink } from "lucide-react"
import { DashboardHeader } from "@/components/dashboard-header"
import { DashboardNav } from "@/components/dashboard-nav"
import Link from "next/link"

export default function EvidencePage() {
  return (
    <div className="flex min-h-screen flex-col">
      <DashboardHeader />
      <div className="flex flex-1">
        <DashboardNav />
        <main className="flex-1 p-6">
          <div className="flex flex-col gap-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Link href="/dashboard">
                  <Button variant="ghost" size="icon">
                    <ArrowLeft className="h-5 w-5" />
                  </Button>
                </Link>
                <h1 className="text-2xl font-bold">Medical Evidence Search</h1>
              </div>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Search PubMed</CardTitle>
                <CardDescription>Find authoritative medical evidence related to your health</CardDescription>
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

                  <div className="space-y-2">
                    <h3 className="text-sm font-medium">Popular Topics</h3>
                    <div className="flex flex-wrap gap-2">
                      <Button variant="outline" size="sm">
                        Vitamin D Deficiency
                      </Button>
                      <Button variant="outline" size="sm">
                        Hypertension
                      </Button>
                      <Button variant="outline" size="sm">
                        Cholesterol Management
                      </Button>
                      <Button variant="outline" size="sm">
                        Diabetes Type 2
                      </Button>
                      <Button variant="outline" size="sm">
                        Weight Management
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Recent Searches</CardTitle>
                <CardDescription>Your recent evidence searches</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="rounded-lg border p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-medium">Vitamin D Deficiency Treatment</h3>
                        <p className="text-xs text-muted-foreground mt-1">Searched on Apr 16, 2023 • 12 results</p>
                      </div>
                      <Button variant="outline" size="sm">
                        <Search className="h-4 w-4 mr-1" />
                        View Results
                      </Button>
                    </div>
                  </div>

                  <div className="rounded-lg border p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-medium">Hypertension Management</h3>
                        <p className="text-xs text-muted-foreground mt-1">Searched on Apr 10, 2023 • 24 results</p>
                      </div>
                      <Button variant="outline" size="sm">
                        <Search className="h-4 w-4 mr-1" />
                        View Results
                      </Button>
                    </div>
                  </div>

                  <div className="rounded-lg border p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-medium">Cholesterol Guidelines</h3>
                        <p className="text-xs text-muted-foreground mt-1">Searched on Mar 28, 2023 • 18 results</p>
                      </div>
                      <Button variant="outline" size="sm">
                        <Search className="h-4 w-4 mr-1" />
                        View Results
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Evidence-Based Insights</CardTitle>
                <CardDescription>
                  AI-generated insights based on your health records and medical evidence
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="rounded-lg border p-4">
                    <h3 className="font-medium">Vitamin D Deficiency</h3>
                    <p className="text-sm text-muted-foreground mt-2">
                      Based on your lab results showing Vitamin D level of 24 ng/mL and evidence from recent clinical
                      studies (PMID: 32441348, 31690364), supplementation of 2000-4000 IU daily is recommended for
                      adults with levels below 30 ng/mL. A meta-analysis of 25 randomized controlled trials found this
                      dosage effective for raising levels to the optimal range within 2-3 months.
                    </p>
                    <div className="mt-3 flex gap-2">
                      <Button size="sm" variant="outline">
                        <ExternalLink className="h-4 w-4 mr-1" />
                        View PubMed Studies
                      </Button>
                      <Button size="sm" variant="outline">
                        View Related Records
                      </Button>
                    </div>
                  </div>

                  <div className="rounded-lg border p-4">
                    <h3 className="font-medium">Blood Pressure Management</h3>
                    <p className="text-sm text-muted-foreground mt-2">
                      Your records indicate elevated blood pressure (138/88 mmHg). According to the latest AHA
                      guidelines (PMID: 31992388) and a systematic review of 123 studies (PMID: 30571591), lifestyle
                      modifications are recommended as first-line intervention for readings in the 130-139/80-89 mmHg
                      range. These include reduced sodium intake, increased physical activity, and the DASH diet, which
                      have shown to reduce systolic BP by 5-10 mmHg in clinical trials.
                    </p>
                    <div className="mt-3 flex gap-2">
                      <Button size="sm" variant="outline">
                        <ExternalLink className="h-4 w-4 mr-1" />
                        View PubMed Studies
                      </Button>
                      <Button size="sm" variant="outline">
                        View Related Records
                      </Button>
                    </div>
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
