'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { FileUp, FileText, AlertCircle, CheckCircle, Brain, Clock } from 'lucide-react';
import apiClient, { AvailableModels } from '@/lib/api-client';
import { useApi, useFileUpload } from '@/hooks/use-api';

interface SummaryResult {
  summary: string;
  model_used: string;
  provider: string;
  processing_time_seconds: number;
}

export function PdfSummarizer() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<'openai' | 'google' | 'anthropic'>('openai');
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [summary, setSummary] = useState<SummaryResult | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Fetch available models
  const {
    data: models,
    loading: modelsLoading,
    execute: fetchModels,
    error: modelsError
  } = useApi<AvailableModels>(apiClient.getAvailableModels);

  // PDF summarization
  const {
    upload: summarizePdf,
    uploading: summarizing,
    progress,
    error: summaryError,
    result: summaryResult,
    reset: resetSummary
  } = useFileUpload<SummaryResult>((file: File) => 
    apiClient.summarizePdf(file, selectedProvider, selectedModel)
  );

  // Load models on component mount
  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  // Update selected model when provider changes
  useEffect(() => {
    if (models && models[selectedProvider] && models[selectedProvider].length > 0) {
      setSelectedModel(models[selectedProvider][0].id);
    }
  }, [selectedProvider, models]);

  // Update summary when result changes
  useEffect(() => {
    if (summaryResult) {
      setSummary(summaryResult);
    }
  }, [summaryResult]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
      setSummary(null);
      resetSummary();
    } else if (file) {
      console.error('Please select a PDF file');
    }
  };

  const handleSummarize = async () => {
    if (!selectedFile || !selectedModel) {
      return;
    }

    try {
      await summarizePdf(selectedFile);
    } catch (error) {
      console.error('Summarization failed:', error);
    }
  };

  const triggerFileSelect = () => {
    fileInputRef.current?.click();
  };

  const getAvailableModels = () => {
    if (!models || !models[selectedProvider]) return [];
    return models[selectedProvider];
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            PDF Medical Summary
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* File Upload */}
          <div>
            <Label>PDF Document</Label>
            <div
              className="border-2 border-dashed rounded-lg p-6 text-center cursor-pointer hover:bg-slate-50 transition-colors mt-2"
              onClick={triggerFileSelect}
            >
              {selectedFile ? (
                <div className="flex items-center justify-center gap-2">
                  <FileText className="h-6 w-6 text-blue-600" />
                  <span className="font-medium">{selectedFile.name}</span>
                  <span className="text-sm text-muted-foreground">
                    ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
                  </span>
                </div>
              ) : (
                <>
                  <FileUp className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
                  <p className="text-sm font-medium mb-1">Click to select PDF file</p>
                  <p className="text-xs text-muted-foreground">Medical reports, lab results, discharge summaries, etc.</p>
                </>
              )}
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf,.pdf"
              onChange={handleFileSelect}
              className="hidden"
            />
          </div>

          {/* Provider Selection */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>AI Provider</Label>
              <Select 
                value={selectedProvider} 
                onValueChange={(value: 'openai' | 'google' | 'anthropic') => setSelectedProvider(value)}
                disabled={summarizing}
              >
                <SelectTrigger className="mt-2">
                  <SelectValue placeholder="Select provider" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="openai">OpenAI (GPT)</SelectItem>
                  <SelectItem value="google">Google (Gemini)</SelectItem>
                  <SelectItem value="anthropic">Anthropic (Claude)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>Model</Label>
              <Select 
                value={selectedModel} 
                onValueChange={setSelectedModel}
                disabled={summarizing || modelsLoading}
              >
                <SelectTrigger className="mt-2">
                  <SelectValue placeholder="Select model" />
                </SelectTrigger>
                <SelectContent>
                  {getAvailableModels().map((model) => (
                    <SelectItem key={model.id} value={model.id}>
                      {model.name}
                      {model.vision_capable && (
                        <span className="ml-2 text-xs text-blue-600">(Vision)</span>
                      )}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Models Loading/Error */}
          {modelsLoading && (
            <p className="text-sm text-muted-foreground">Loading available models...</p>
          )}
          
          {modelsError && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Failed to load models: {modelsError.detail}
              </AlertDescription>
            </Alert>
          )}

          {/* Summarize Button */}
          <Button
            onClick={handleSummarize}
            className="w-full"
            disabled={!selectedFile || !selectedModel || summarizing}
          >
            {summarizing ? (
              <>
                <Brain className="mr-2 h-4 w-4 animate-pulse" />
                Analyzing PDF...
              </>
            ) : (
              <>
                <Brain className="mr-2 h-4 w-4" />
                Generate Medical Summary
              </>
            )}
          </Button>

          {/* Progress */}
          {summarizing && (
            <div className="space-y-2">
              <Progress value={progress} />
              <p className="text-xs text-center text-muted-foreground">
                Processing with {selectedProvider} {selectedModel}... {progress}%
              </p>
            </div>
          )}

          {/* Error */}
          {summaryError && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Summarization failed: {summaryError.detail}
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Summary Result */}
      {summary && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                Medical Summary
              </div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Clock className="h-4 w-4" />
                {summary.processing_time_seconds.toFixed(1)}s
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                <span>Provider: <strong>{summary.provider}</strong></span>
                <span>Model: <strong>{summary.model_used}</strong></span>
              </div>
              
              <div>
                <Label>AI-Generated Summary</Label>
                <Textarea
                  value={summary.summary}
                  readOnly
                  className="mt-2 min-h-[200px] resize-none"
                  placeholder="Summary will appear here..."
                />
              </div>
              
              <div className="flex gap-2">
                <Button 
                  variant="outline" 
                  onClick={() => navigator.clipboard.writeText(summary.summary)}
                >
                  Copy Summary
                </Button>
                <Button 
                  variant="outline"
                  onClick={() => {
                    const blob = new Blob([summary.summary], { type: 'text/plain' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `${selectedFile?.name || 'document'}_summary.txt`;
                    a.click();
                    URL.revokeObjectURL(url);
                  }}
                >
                  Download Summary
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}