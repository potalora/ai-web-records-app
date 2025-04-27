'use client';

import { useState, ChangeEvent, FormEvent, useEffect, useCallback } from 'react';
import axios from 'axios';
import FileUpload from './components/FileUpload';
import ProviderModelSelector from './components/ProviderModelSelector';
import SummaryDisplay from './components/SummaryDisplay';

interface PubMedArticle {
  pmid: string | null;
  title: string | null;
  abstract: string | null; 
}

type Provider = 'openai' | 'google' | 'anthropic';

// Removed AvailableModels interface, now internal to ProviderModelSelector

export default function Home() {
  const [message, setMessage] = useState<string>('Click the button to fetch message from backend.');
  const [backendError, setBackendError] = useState<string | null>(null); // Renamed for clarity
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [summary, setSummary] = useState<string | null>(null);
  const [isLoadingSummary, setIsLoadingSummary] = useState<boolean>(false);
  const [summaryError, setSummaryError] = useState<string | null>(null); // Specific error for summary
  const [selectedProvider, setSelectedProvider] = useState<Provider>('openai');
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [modelLoadingError, setModelLoadingError] = useState<string | null>(null); // Error from model loader

  // Removed states related to available models and current provider models
  // Removed useEffects for fetching and managing model lists (now in ProviderModelSelector)

  const [pubmedQuery, setPubmedQuery] = useState<string>('');
  const [pubmedResults, setPubmedResults] = useState<PubMedArticle[]>([]);
  const [isLoadingPubMed, setIsLoadingPubMed] = useState<boolean>(false);
  const [pubmedError, setPubmedError] = useState<string | null>(null);

  const fetchMessage = async () => {
    setBackendError(null);
    // Reset other states if needed
    setSummary(null);
    setSummaryError(null);
    setPubmedError(null);
    setPubmedResults([]);
    setMessage('Fetching...');
    try {
      const response = await axios.get('/api/proxy?target=http://localhost:8000/hello'); // Using proxy
      setMessage(response.data.message);
    } catch (err) {
      console.error("Error fetching message:", err);
      setBackendError('Failed to fetch message from backend. Is the backend running and proxy configured?');
      setMessage('Click the button to fetch message from backend.');
    }
  };

  // Renamed handleFileChange to match prop name expected by FileUpload
  const onFileSelect = useCallback((file: File | null) => {
    setSelectedFile(file);
    setSummary(null); // Clear previous summary on new file selection
    setSummaryError(null);
  }, []); // Added useCallback for stability if passed deep down

  const handleSummarize = async () => {
    if (!selectedFile) {
      setSummaryError('Please select a PDF file first.');
      return;
    }
    if (!selectedProvider || !selectedModel) {
      setSummaryError('Please select a provider and model first.');
      return;
    }

    setSummaryError(null);
    setSummary(null);
    setIsLoadingSummary(true);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('provider', selectedProvider);
    formData.append('model', selectedModel);

    try {
      // Using proxy for the summarization call as well
      const response = await axios.post('/api/proxy?target=http://localhost:8000/summarize-pdf/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setSummary(response.data.summary);
    } catch (err: any) {
      console.error("Error summarizing PDF:", err);
      setSummaryError(err.response?.data?.detail || 'Failed to summarize PDF. Check backend logs.');
    } finally {
      setIsLoadingSummary(false);
    }
  };

  // Renamed handler functions passed to ProviderModelSelector
  const handleProviderSelect = useCallback((provider: Provider) => {
    setSelectedProvider(provider);
    setSummary(null); // Clear summary when provider changes
    setSummaryError(null);
  }, []);

  const handleModelSelect = useCallback((model: string) => {
    setSelectedModel(model);
    setSummary(null); // Clear summary when model changes
    setSummaryError(null);
  }, []);

  const handlePubMedSearch = async (event: FormEvent) => {
    event.preventDefault(); 
    if (!pubmedQuery.trim()) {
      setPubmedError('Please enter a search query.');
      return;
    }

    // Reset other potential errors/results
    setBackendError(null);
    setSummary(null);
    setSummaryError(null); 
    
    setPubmedError(null);
    setPubmedResults([]);
    setIsLoadingPubMed(true);

    try {
      // Using proxy for PubMed search
      const response = await axios.post('/api/proxy?target=http://localhost:8000/retrieve-evidence/pubmed', {
        query: pubmedQuery,
        max_results: 5 
      });
      setPubmedResults(response.data);
    } catch (err: any) {
      console.error("Error searching PubMed:", err);
      const errorDetail = err.response?.data?.detail;
      if (axios.isAxiosError(err) && err.response?.status === 404) {
          setPubmedError(errorDetail || `No PubMed articles found for "${pubmedQuery}".`);
      } else {
          setPubmedError(errorDetail || 'Failed to search PubMed. Check backend connection and query.');
      }
    } finally {
      setIsLoadingPubMed(false);
    }
  };

  // Improved layout using grid for better responsiveness maybe later
  return (
    <main className="flex min-h-screen flex-col items-center justify-start p-6 sm:p-12 bg-gradient-to-br from-gray-100 to-blue-100">
      <h1 className="text-3xl sm:text-4xl font-bold mb-8 text-gray-800 text-center">AI Health Records App</h1>

      {/* Grid container for layout */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-4xl">

        {/* Column 1: Upload, Select, Summarize */}
        <div className="bg-white p-6 rounded-lg shadow-md flex flex-col space-y-4">
          <h2 className="text-xl sm:text-2xl font-semibold mb-4 text-gray-700 border-b pb-2">Process Document</h2>
          
          <FileUpload onFileChange={onFileSelect} acceptedFileType="application/pdf,text/plain,image/jpeg,image/png" />

          <ProviderModelSelector 
            selectedProvider={selectedProvider}
            selectedModel={selectedModel}
            onProviderChange={handleProviderSelect}
            onModelChange={handleModelSelect}
            setLoadingError={setModelLoadingError}
          />
          {modelLoadingError && <p className="text-xs text-red-600">Model Loading Error: {modelLoadingError}</p>}

          <button
            onClick={handleSummarize}
            disabled={!selectedFile || !selectedModel || isLoadingSummary} 
            className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoadingSummary ? 'Summarizing...' : 'Summarize Document'}
          </button>

          <SummaryDisplay 
             summary={summary} 
             isLoading={isLoadingSummary} 
             error={summaryError} 
           />
        </div>

        {/* Column 2: PubMed Search & Connection Test */}
        <div className="bg-white p-6 rounded-lg shadow-md flex flex-col space-y-4">
          <h2 className="text-xl sm:text-2xl font-semibold mb-4 text-gray-700 border-b pb-2">PubMed Search</h2>
          <form onSubmit={handlePubMedSearch} className="flex flex-col space-y-3">
            <input
              type="text"
              value={pubmedQuery}
              onChange={(e) => setPubmedQuery(e.target.value)}
              placeholder="Search PubMed articles..."
              className="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg p-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <button
              type="submit"
              disabled={isLoadingPubMed}
              className="w-full px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoadingPubMed ? 'Searching...' : 'Search PubMed'}
            </button>
          </form>
          {pubmedError && <p className="mt-2 text-red-600 text-sm">Error: {pubmedError}</p>}
          {isLoadingPubMed && <p className="mt-2 text-gray-600 text-sm animate-pulse">Loading PubMed results...</p>}
          {pubmedResults.length > 0 && (
            <div className="mt-4 max-h-60 overflow-y-auto border rounded-md p-3 space-y-2 bg-gray-50">
              <h3 className="text-md font-semibold text-gray-700">Results:</h3>
              {pubmedResults.map((article, index) => (
                <div key={article.pmid || index} className="text-xs border-b pb-1 last:border-b-0">
                  <p className="font-medium text-gray-800">{article.title || 'No Title'}</p>
                  {/* Optionally show abstract <p className="text-gray-600 mt-1">{article.abstract || 'No Abstract'}</p> */}
                  {article.pmid && <a href={`https://pubmed.ncbi.nlm.nih.gov/${article.pmid}/`} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">PMID: {article.pmid}</a>}
                </div>
              ))}
            </div>
          )}

          {/* Connection Test Section - Kept separate for clarity */}
          <div className="pt-4 mt-4 border-t">
             <h2 className="text-lg font-semibold mb-2 text-gray-700">Backend Test</h2>
             <button
               onClick={fetchMessage}
               className="w-full px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-700 transition-colors mb-2"
             >
               Call Backend /hello
             </button>
             {backendError && <p className="mt-2 text-red-600 text-sm">Error: {backendError}</p>}
             <p className="mt-2 text-sm text-gray-600">{message}</p>
          </div>
        </div>

      </div> 
      {/* End Grid */}
    </main>
  );
}
