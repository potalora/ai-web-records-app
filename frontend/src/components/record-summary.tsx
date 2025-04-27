export function RecordSummary({ recordId }: { recordId: string }) {
  // This would normally fetch summary based on the record ID
  return (
    <div className="space-y-4">
      <div className="rounded-md bg-slate-50 p-4">
        <h3 className="font-medium mb-2">Summary</h3>
        <p className="text-sm text-muted-foreground">
          This Complete Blood Count (CBC) shows normal values for most parameters, including white blood cells, red
          blood cells, hemoglobin, hematocrit, and platelets. However, your Vitamin D level is low at 24 ng/mL
          (reference range: 30-100 ng/mL), indicating a mild deficiency. All other measured values are within normal
          ranges.
        </p>
      </div>

      <div className="rounded-md bg-slate-50 p-4">
        <h3 className="font-medium mb-2">Clinical Significance</h3>
        <p className="text-sm text-muted-foreground">
          The low Vitamin D level may contribute to symptoms such as fatigue, muscle weakness, or bone pain if present.
          Vitamin D is essential for calcium absorption and bone health. Deficiency is common, especially in regions
          with limited sun exposure or in individuals with certain dietary restrictions.
        </p>
      </div>

      <div className="rounded-md bg-slate-50 p-4">
        <h3 className="font-medium mb-2">Evidence-Based Insights</h3>
        <p className="text-sm text-muted-foreground">
          According to recent clinical studies (PMID: 32441348, 31690364), vitamin D supplementation of 2000-4000 IU
          daily is recommended for adults with levels below 30 ng/mL. A meta-analysis of 25 randomized controlled trials
          found this dosage effective for raising levels to the optimal range within 2-3 months.
        </p>
      </div>
    </div>
  )
}
