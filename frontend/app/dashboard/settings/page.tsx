import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ArrowLeft } from "lucide-react"
import { DashboardHeader } from "@/components/dashboard-header"
import { DashboardNav } from "@/components/dashboard-nav"
import Link from "next/link"

export default function SettingsPage() {
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
                <h1 className="text-2xl font-bold">Settings</h1>
              </div>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Application Settings</CardTitle>
                <CardDescription>Configure your HealthAI experience</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Theme</label>
                    <select className="w-full rounded-md border border-input bg-background px-3 py-2">
                      <option value="light">Light</option>
                      <option value="dark">Dark</option>
                      <option value="system">System</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Default Summary View</label>
                    <select className="w-full rounded-md border border-input bg-background px-3 py-2">
                      <option value="detailed">Detailed</option>
                      <option value="concise">Concise</option>
                      <option value="technical">Technical</option>
                      <option value="simplified">Simplified</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Evidence Sources</label>
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <input type="checkbox" id="pubmed" className="rounded border-gray-300" defaultChecked />
                        <label htmlFor="pubmed" className="text-sm">
                          PubMed
                        </label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <input type="checkbox" id="cochrane" className="rounded border-gray-300" defaultChecked />
                        <label htmlFor="cochrane" className="text-sm">
                          Cochrane Library
                        </label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <input type="checkbox" id="medline" className="rounded border-gray-300" defaultChecked />
                        <label htmlFor="medline" className="text-sm">
                          MEDLINE
                        </label>
                      </div>
                    </div>
                  </div>

                  <div className="pt-4">
                    <Button>Save Settings</Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Data Management</CardTitle>
                <CardDescription>Manage your health data</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="rounded-md bg-slate-50 p-4">
                    <h3 className="font-medium mb-2">Export Data</h3>
                    <p className="text-sm text-muted-foreground mb-4">
                      Download all your health records and summaries in a portable format.
                    </p>
                    <div className="flex gap-2">
                      <Button variant="outline">Export as PDF</Button>
                      <Button variant="outline">Export as JSON</Button>
                    </div>
                  </div>

                  <div className="rounded-md bg-slate-50 p-4">
                    <h3 className="font-medium mb-2">Clear Data</h3>
                    <p className="text-sm text-muted-foreground mb-4">
                      Remove all your health records and generated summaries from the application.
                    </p>
                    <Button variant="destructive">Clear All Data</Button>
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
