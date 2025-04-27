import { Brain, FileText, Pill } from "lucide-react"
import { Button } from "@/components/ui/button"

export function RecentInsights() {
  const insights = [
    {
      id: 1,
      type: "diagnostic",
      title: "Vitamin D Deficiency",
      description:
        "Your lab results indicate vitamin D deficiency, which may contribute to fatigue and muscle weakness.",
      date: "April 16, 2023",
      source: "Complete Blood Count (Apr 15, 2023)",
      icon: <Brain className="h-5 w-5 text-teal-600" />,
    },
    {
      id: 2,
      type: "treatment",
      title: "Blood Pressure Management",
      description:
        "Based on your elevated blood pressure readings, dietary changes and regular exercise are recommended.",
      date: "February 12, 2023",
      source: "Annual Physical Exam (Feb 10, 2023)",
      icon: <Pill className="h-5 w-5 text-purple-600" />,
    },
    {
      id: 3,
      type: "summary",
      title: "Annual Health Review",
      description: "Overall health status is good with minor concerns about blood pressure and vitamin levels.",
      date: "February 11, 2023",
      source: "Multiple Records Analysis",
      icon: <FileText className="h-5 w-5 text-blue-600" />,
    },
  ]

  return (
    <div className="space-y-4">
      {insights.map((insight) => (
        <div key={insight.id} className="rounded-lg border p-4">
          <div className="flex items-start gap-3">
            <div className="rounded-full bg-slate-100 p-2">{insight.icon}</div>
            <div className="flex-1">
              <div className="flex justify-between items-start">
                <h3 className="font-medium">{insight.title}</h3>
                <span className="text-xs text-muted-foreground">{insight.date}</span>
              </div>
              <p className="text-sm text-muted-foreground mt-1">{insight.description}</p>
              <p className="text-xs text-muted-foreground mt-2">Source: {insight.source}</p>
              <div className="mt-3">
                <Button size="sm" variant="outline">
                  View Details
                </Button>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
