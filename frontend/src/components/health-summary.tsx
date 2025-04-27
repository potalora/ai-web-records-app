import { Card } from "@/components/ui/card"

export function HealthSummary() {
  return (
    <div className="space-y-4">
      <Card className="p-4 bg-slate-50">
        <h3 className="font-medium mb-2">Summary</h3>
        <p className="text-sm text-muted-foreground">
          Based on your medical records, you are a 42-year-old individual with generally good health but showing early
          signs of hypertension and vitamin D deficiency. Your cholesterol levels are within normal ranges, and you have
          no significant chronic conditions. Your BMI is slightly elevated at 26.4, indicating you are overweight but
          not obese.
        </p>
      </Card>

      <Card className="p-4 bg-slate-50">
        <h3 className="font-medium mb-2">Key Health Indicators</h3>
        <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
          <li>Blood Pressure: Elevated (138/88 mmHg)</li>
          <li>Cholesterol: Normal (Total: 175 mg/dL, LDL: 100 mg/dL)</li>
          <li>Vitamin D: Low (24 ng/mL)</li>
          <li>BMI: 26.4 (Overweight)</li>
          <li>Blood Glucose: Normal (92 mg/dL fasting)</li>
        </ul>
      </Card>

      <Card className="p-4 bg-slate-50">
        <h3 className="font-medium mb-2">Evidence-Based Insights</h3>
        <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
          <li>
            <strong>Vitamin D Deficiency:</strong> Recent studies from PubMed (PMID: 32441348) suggest supplementation
            of 2000-4000 IU daily for adults with levels below 30 ng/mL.
          </li>
          <li>
            <strong>Blood Pressure:</strong> The latest AHA guidelines (PMID: 31992388) recommend lifestyle
            modifications as first-line intervention for readings in the 130-139/80-89 mmHg range.
          </li>
        </ul>
      </Card>
    </div>
  )
}
