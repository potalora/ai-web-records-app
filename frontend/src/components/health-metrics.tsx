export function HealthMetrics() {
  const metrics = [
    {
      name: "Blood Pressure",
      value: "138/88",
      unit: "mmHg",
      status: "Elevated",
      change: "↑ 5 points from last reading",
    },
    {
      name: "Total Cholesterol",
      value: "175",
      unit: "mg/dL",
      status: "Normal",
      change: "↓ 10 points from last reading",
    },
    {
      name: "Blood Glucose",
      value: "92",
      unit: "mg/dL",
      status: "Normal",
      change: "No significant change",
    },
    {
      name: "Vitamin D",
      value: "24",
      unit: "ng/mL",
      status: "Low",
      change: "↓ 2 points from last reading",
    },
    {
      name: "BMI",
      value: "26.4",
      unit: "",
      status: "Overweight",
      change: "↑ 0.2 from last reading",
    },
  ]

  return (
    <div className="space-y-4">
      {metrics.map((metric, index) => (
        <div key={index} className="flex justify-between items-center p-2 rounded-md hover:bg-slate-50">
          <div>
            <p className="font-medium">{metric.name}</p>
            <p className="text-xs text-muted-foreground">{metric.change}</p>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-2">
              <p className="font-bold">
                {metric.value} {metric.unit}
              </p>
              <StatusBadge status={metric.status} />
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  let bgColor = "bg-green-100"
  let textColor = "text-green-800"

  if (status === "Elevated" || status === "Low" || status === "Overweight") {
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
