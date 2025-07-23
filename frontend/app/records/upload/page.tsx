import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { ArrowLeft, FileUp } from "lucide-react"
import { DashboardHeader } from "@/components/dashboard-header"
import { DashboardNav } from "@/components/dashboard-nav"
import { UploadCard } from "@/components/upload-card"
import Link from "next/link"

export default function UploadPage() {
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
                <h1 className="text-2xl font-bold">Upload Medical Records</h1>
              </div>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Upload Files</CardTitle>
                <CardDescription>Upload your medical records for analysis</CardDescription>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="file" className="space-y-4">
                  <TabsList>
                    <TabsTrigger value="file">File Upload</TabsTrigger>
                    <TabsTrigger value="ehr">EHR Import</TabsTrigger>
                    <TabsTrigger value="text">Text Input</TabsTrigger>
                  </TabsList>

                  <TabsContent value="file">
                    <UploadCard />
                  </TabsContent>

                  <TabsContent value="ehr">
                    <div className="space-y-4">
                      <div className="rounded-lg border p-4">
                        <h3 className="text-lg font-medium mb-2">Connect to EHR System</h3>
                        <p className="text-sm text-muted-foreground mb-4">
                          Import your medical records directly from your healthcare provider's Electronic Health Record
                          system.
                        </p>
                        <div className="grid gap-4 md:grid-cols-2">
                          <div className="rounded-md border p-3 flex items-center gap-3 cursor-pointer hover:bg-slate-50">
                            <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                              <span className="font-bold text-blue-600">E</span>
                            </div>
                            <div>
                              <p className="font-medium">Epic MyChart</p>
                              <p className="text-xs text-muted-foreground">Connect to Epic Systems</p>
                            </div>
                          </div>
                          <div className="rounded-md border p-3 flex items-center gap-3 cursor-pointer hover:bg-slate-50">
                            <div className="h-10 w-10 rounded-full bg-green-100 flex items-center justify-center">
                              <span className="font-bold text-green-600">C</span>
                            </div>
                            <div>
                              <p className="font-medium">Cerner</p>
                              <p className="text-xs text-muted-foreground">Connect to Cerner</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </TabsContent>

                  <TabsContent value="text">
                    <div className="space-y-4">
                      <div className="space-y-2">
                        <label htmlFor="text-type" className="text-sm font-medium">
                          Record Type
                        </label>
                        <select
                          id="text-type"
                          className="w-full rounded-md border border-input bg-background px-3 py-2"
                        >
                          <option value="lab-results">Lab Results</option>
                          <option value="medical-notes">Medical Notes</option>
                          <option value="medication-list">Medication List</option>
                          <option value="discharge-summary">Discharge Summary</option>
                        </select>
                      </div>
                      <textarea
                        className="min-h-[200px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                        placeholder="Enter your medical notes, lab results, or other text data here..."
                      />
                      <div className="flex justify-end">
                        <Button>
                          <FileUp className="mr-2 h-4 w-4" />
                          Analyze Text
                        </Button>
                      </div>
                    </div>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Upload Guidelines</CardTitle>
                <CardDescription>Tips for getting the best results from your uploads</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="rounded-md bg-slate-50 p-4">
                    <h3 className="font-medium mb-2">Supported File Types</h3>
                    <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                      <li>PDF documents (medical reports, lab results)</li>
                      <li>Images (JPEG, PNG - for scanned documents)</li>
                      <li>EHR exports (CCD, FHIR, HL7 formats)</li>
                      <li>Plain text files (TXT)</li>
                    </ul>
                  </div>

                  <div className="rounded-md bg-slate-50 p-4">
                    <h3 className="font-medium mb-2">Best Practices</h3>
                    <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                      <li>Ensure documents are clearly legible</li>
                      <li>Include complete documents rather than partial pages</li>
                      <li>Make sure scanned images are in focus and well-lit</li>
                      <li>Organize related documents together for better analysis</li>
                    </ul>
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
