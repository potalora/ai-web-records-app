import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { DashboardHeader } from "@/components/dashboard-header"
import { DashboardNav } from "@/components/dashboard-nav"
import { UploadCard } from "@/components/upload-card"

export default function UploadPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <DashboardHeader />
      <div className="flex flex-1">
        <DashboardNav />
        <main className="flex-1 p-6">
          <div className="flex flex-col gap-6">
            <div className="flex items-center justify-between">
              <h1 className="text-3xl font-bold">Upload Medical Data</h1>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Upload Files</CardTitle>
                <CardDescription>Upload your medical records for AI analysis</CardDescription>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="file" className="space-y-4">
                  <TabsList>
                    <TabsTrigger value="file">File Upload</TabsTrigger>
                    <TabsTrigger value="text">Text Input</TabsTrigger>
                    <TabsTrigger value="camera">Camera</TabsTrigger>
                  </TabsList>

                  <TabsContent value="file">
                    <UploadCard />
                  </TabsContent>

                  <TabsContent value="text">
                    <div className="space-y-4">
                      <textarea
                        className="min-h-[200px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                        placeholder="Enter your medical notes, symptoms, or other text data here..."
                      />
                      <div className="flex justify-end">
                        <button className="rounded-md bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700">
                          Analyze Text
                        </button>
                      </div>
                    </div>
                  </TabsContent>

                  <TabsContent value="camera">
                    <div className="space-y-4 text-center">
                      <div className="aspect-video bg-slate-100 rounded-lg flex items-center justify-center">
                        <p className="text-muted-foreground">Camera preview will appear here</p>
                      </div>
                      <button className="rounded-md bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700">
                        Take Photo
                      </button>
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
                      <li>Images (JPEG, PNG - for scanned documents or medical images)</li>
                      <li>DICOM files (for medical imaging like X-rays, MRIs)</li>
                      <li>EHR exports (from electronic health record systems)</li>
                      <li>Plain text files (TXT)</li>
                    </ul>
                  </div>

                  <div className="rounded-md bg-slate-50 p-4">
                    <h3 className="font-medium mb-2">Best Practices</h3>
                    <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                      <li>Ensure documents are clearly legible</li>
                      <li>Include complete documents rather than partial pages</li>
                      <li>Make sure images are in focus and well-lit</li>
                      <li>Organize related documents together for better analysis</li>
                      <li>Remove any sensitive information not relevant to your health</li>
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
