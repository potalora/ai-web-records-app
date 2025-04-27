import { FileText, FileImage, FileArchive } from "lucide-react"

export function RecentUploads() {
  const uploads = [
    {
      id: 1,
      name: "Blood Test Results.pdf",
      type: "pdf",
      date: "2 hours ago",
      status: "Analyzed",
    },
    {
      id: 2,
      name: "MRI Scan.dicom",
      type: "dicom",
      date: "1 day ago",
      status: "Analyzed",
    },
    {
      id: 3,
      name: "Doctor Notes.pdf",
      type: "pdf",
      date: "3 days ago",
      status: "Analyzed",
    },
    {
      id: 4,
      name: "X-Ray Image.jpg",
      type: "image",
      date: "1 week ago",
      status: "Analyzed",
    },
  ]

  return (
    <div className="space-y-4">
      {uploads.length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-4">
          No recent uploads found. Upload medical data to get started.
        </p>
      ) : (
        <div className="space-y-2">
          {uploads.map((upload) => (
            <div key={upload.id} className="flex items-center p-2 hover:bg-slate-50 rounded-md">
              {upload.type === "pdf" ? (
                <FileText className="h-5 w-5 mr-3 text-red-500" />
              ) : upload.type === "image" ? (
                <FileImage className="h-5 w-5 mr-3 text-blue-500" />
              ) : (
                <FileArchive className="h-5 w-5 mr-3 text-amber-500" />
              )}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{upload.name}</p>
                <p className="text-xs text-muted-foreground">{upload.date}</p>
              </div>
              <div className="ml-2">
                <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
                  {upload.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
