import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { ArrowLeft, Download, Share, Search } from "lucide-react"
import { DashboardHeader } from "@/components/dashboard-header"
import { DashboardNav } from "@/components/dashboard-nav"
import Link from "next/link"
import { MedicalRecordViewer } from "@/components/medical-record-viewer"
import { RecordSummary } from "@/components/record-summary"

export default function RecordDetailPage({ params }: { params: { id: string } }) {
  // This would normally fetch the record based on the ID
  const record = {
    id: params.id,
    name: "Complete Blood Count",
    type: "Lab Results",
    date: "April 15, 2023",
    provider: "Quest Diagnostics",
    status: "Analyzed",
    description: "Routine blood work as part of annual physical examination",
    results: [
      { name: "White Blood Cell Count", value: "7.5", unit: "x10^9/L", range: "4.5-11.0", status: "Normal" },
      { name: "Red Blood Cell Count", value: "5.2", unit: "x10^12/L", range: "4.5-5.9", status: "Normal" },
      { name: "Hemoglobin", value: "14.2", unit: "g/dL", range: "13.5-17.5", status: "Normal" },
      { name: "Hematocrit", value: "42", unit: "%", range: "41-50", status: "Normal" },
      { name: "Platelet Count", value: "250", unit: "x10^9/L", range: "150-450", status: "Normal" },
      { name: "Vitamin D, 25-OH", value: "24", unit: "ng/mL", range: "30-100", status: "Low" },
      { name: "Vitamin B12", value: "450", unit: "pg/mL", range: "200-900", status: "Normal" },
      { name: "Ferritin", value: "120", unit: "ng/mL", range: "30-400", status: "Normal" },
    ],
  }

  return (
    <div className="flex min-h-screen flex-col">
      <DashboardHeader />
      <div className="flex flex-1">
        <DashboardNav />
        <main className="flex-1 p-6">
          <div className="flex flex-col gap-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Link href="/dashboard/records">
                  <Button variant="ghost" size="icon">
                    <ArrowLeft className="h-5 w-5" />
                  </Button>
                </Link>
                <h1 className="text-2xl font-bold">{record.name}</h1>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm">
                  <Download className="h-4 w-4 mr-2" />
                  Download
                </Button>
                <Button variant="outline" size="sm">
                  <Share className="h-4 w-4 mr-2" />
                  Share
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>Record Details</CardTitle>
                </CardHeader>
                <CardContent>
                  <dl className="space-y-2">
                    <div className="flex justify-between">
                      <dt className="font-medium">Type:</dt>
                      <dd className="text-muted-foreground">{record.type}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="font-medium">Date:</dt>
                      <dd className="text-muted-foreground">{record.date}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="font-medium">Provider:</dt>
                      <dd className="text-muted-foreground">{record.provider}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="font-medium">Status:</dt>
                      <dd>
                        <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
                          {record.status}
                        </span>
                      </dd>
                    </div>
                  </dl>
                </CardContent>
              </Card>

              <Card className="md:col-span-2">
                <CardHeader>
                  <CardTitle>Description</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">{record.description}</p>
                </CardContent>
              </Card>
            </div>

            <Tabs defaultValue="record" className="space-y-4">
              <TabsList>
                <TabsTrigger value="record">Record View</TabsTrigger>
                <TabsTrigger value="summary">AI Summary</TabsTrigger>
                <TabsTrigger value="evidence">Related Evidence</TabsTrigger>
              </TabsList>

              <TabsContent value="record" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Lab Results</CardTitle>
                    <CardDescription>Complete Blood Count from {record.date}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <MedicalRecordViewer results={record.results} />
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="summary" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>AI Summary</CardTitle>
                    <CardDescription>Insights generated from your lab results</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <RecordSummary recordId={record.id} />
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="evidence" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Related Medical Evidence</CardTitle>
                    <CardDescription>Relevant research from PubMed</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex gap-2">
                        <input
                          type="text"
                          placeholder="Search for related evidence..."
                          className="flex-1 rounded-md border border-input bg-background px-3 py-2"
                          defaultValue="Vitamin D deficiency treatment"
                        />
                        <Button>
                          <Search className="h-4 w-4 mr-2" />
                          Search
                        </Button>
                      </div>

                      <div className="space-y-4">
                        <div className="rounded-lg border p-4">
                          <h3 className="font-medium">Vitamin D Supplementation: An Update</h3>
                          <p className="text-xs text-muted-foreground mt-1">
                            Journal of Clinical Endocrinology & Metabolism, 2023
                          </p>
                          <p className="text-sm text-muted-foreground mt-2">
                            This systematic review of 42 randomized controlled trials found that vitamin D
                            supplementation of 2000-4000 IU daily effectively raised serum 25(OH)D levels in adults with
                            deficiency (levels &lt;30 ng/mL).
                          </p>
                          <p className="text-xs mt-2">
                            <span className="font-medium">PMID:</span> 32441348
                          </p>
                          <div className="mt-2">
                            <Button size="sm" variant="outline">
                              View on PubMed
                            </Button>
                          </div>
                        </div>

                        <div className="rounded-lg border p-4">
                          <h3 className="font-medium">Clinical Management of Vitamin D Deficiency in Adults</h3>
                          <p className="text-xs text-muted-foreground mt-1">American Family Physician, 2022</p>
                          <p className="text-sm text-muted-foreground mt-2">
                            This clinical review provides evidence-based guidelines for the management of vitamin D
                            deficiency in adults, including recommended supplementation doses and monitoring protocols.
                          </p>
                          <p className="text-xs mt-2">
                            <span className="font-medium">PMID:</span> 31690364
                          </p>
                          <div className="mt-2">
                            <Button size="sm" variant="outline">
                              View on PubMed
                            </Button>
                          </div>
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
  )
}
