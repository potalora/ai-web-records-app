'use client'

import { useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Loader2, Heart, TrendingUp } from "lucide-react"
import apiClient from "@/lib/api-client"
import { useApi } from "@/hooks/use-api"

export function HealthSummary() {
  const {
    data: healthSummary,
    loading,
    execute: fetchHealthSummary,
    error
  } = useApi(apiClient.getHealthSummary);

  useEffect(() => {
    fetchHealthSummary();
  }, [fetchHealthSummary]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin" />
        <span className="ml-2 text-sm text-muted-foreground">Loading health summary...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="p-4 bg-red-50">
        <p className="text-sm text-red-600">
          Failed to load health summary: {error.detail}
        </p>
      </Card>
    );
  }

  if (!healthSummary) {
    return (
      <Card className="p-4 bg-slate-50">
        <div className="text-center py-4">
          <Heart className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
          <h3 className="font-medium mb-2">No Health Summary Available</h3>
          <p className="text-sm text-muted-foreground">
            Upload medical records and generate summaries to see your health insights here.
          </p>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <Card className="p-4 bg-slate-50">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-medium">AI Health Summary</h3>
          <div className="flex items-center text-xs text-muted-foreground">
            <TrendingUp className="h-3 w-3 mr-1" />
            {healthSummary.recordsAnalyzed} records analyzed
          </div>
        </div>
        <p className="text-sm text-muted-foreground mb-2">
          {healthSummary.content}
        </p>
        <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t">
          <span>Generated on {formatDate(healthSummary.createdAt)}</span>
          <span>{healthSummary.provider} {healthSummary.model}</span>
        </div>
      </Card>
    </div>
  )
}