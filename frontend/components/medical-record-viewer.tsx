interface Result {
  name: string
  value: string
  unit: string
  range: string
  status: string
}

export function MedicalRecordViewer({ results }: { results: Result[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b">
            <th className="py-2 px-4 text-left font-medium">Test</th>
            <th className="py-2 px-4 text-left font-medium">Result</th>
            <th className="py-2 px-4 text-left font-medium">Unit</th>
            <th className="py-2 px-4 text-left font-medium">Reference Range</th>
            <th className="py-2 px-4 text-left font-medium">Status</th>
          </tr>
        </thead>
        <tbody>
          {results.map((result, index) => (
            <tr key={index} className={index % 2 === 0 ? "bg-slate-50" : ""}>
              <td className="py-2 px-4 font-medium">{result.name}</td>
              <td className="py-2 px-4">{result.value}</td>
              <td className="py-2 px-4 text-muted-foreground">{result.unit}</td>
              <td className="py-2 px-4 text-muted-foreground">{result.range}</td>
              <td className="py-2 px-4">
                <StatusBadge status={result.status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  let bgColor = "bg-green-100"
  let textColor = "text-green-800"

  if (status === "Low" || status === "Borderline") {
    bgColor = "bg-yellow-100"
    textColor = "text-yellow-800"
  } else if (status === "High" || status === "Critical") {
    bgColor = "bg-red-100"
    textColor = "text-red-800"
  }

  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${bgColor} ${textColor}`}>
      {status}
    </span>
  )
}
