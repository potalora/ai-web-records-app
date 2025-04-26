'use client';

import { useState, ChangeEvent } from 'react';
import axios from 'axios';

export default function Home() {
  const [message, setMessage] = useState<string>('Click the button to fetch message from backend.');
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [summary, setSummary] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const fetchMessage = async () => {
    setError(null);
    setSummary(null);
    setMessage('Fetching...');
    try {
      const response = await axios.get('http://localhost:8000/hello');
      setMessage(response.data.message);
    } catch (err) {
      console.error("Error fetching message:", err);
      setError('Failed to fetch message from backend. Is the backend running?');
      setMessage('Click the button to fetch message from backend.');
    }
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setSelectedFile(event.target.files[0]);
      setSummary(null);
      setError(null);
    }
  };

  const handleSummarize = async () => {
    if (!selectedFile) {
      setError('Please select a PDF file first.');
      return;
    }

    setError(null);
    setSummary(null);
    setIsLoading(true);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await axios.post('http://localhost:8000/summarize-pdf/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setSummary(response.data.summary);
    } catch (err: any) {
      console.error("Error summarizing PDF:", err);
      const errorDetail = err.response?.data?.detail || 'Failed to summarize PDF. Check backend logs.';
      setError(`Error: ${errorDetail}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center p-12 space-y-6">
      <h1 className="text-3xl font-bold mb-6">AI Health Records App - PDF Summarizer</h1>

      <div className="w-full max-w-md p-4 border rounded shadow">
        <h2 className="text-xl font-semibold mb-2">Backend Connection Test</h2>
        <button
          onClick={fetchMessage}
          className="w-full px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-700 transition-colors mb-2"
        >
          Call Backend /hello
        </button>
        <p className="text-sm text-gray-600">
          Backend says: {message}
        </p>
        {error && message === 'Click the button to fetch message from backend.' && (
          <p className="text-red-500 mt-1 text-sm">Error: {error}</p>
        )}
      </div>

      <div className="w-full max-w-xl p-6 border rounded shadow">
        <h2 className="text-xl font-semibold mb-4">Upload PDF for Summarization</h2>
        <input
          type="file"
          accept="application/pdf"
          onChange={handleFileChange}
          className="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none p-2 mb-4"
        />
        <button
          onClick={handleSummarize}
          disabled={!selectedFile || isLoading}
          className={`w-full px-4 py-2 text-white rounded transition-colors ${isLoading || !selectedFile ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-500 hover:bg-blue-700'}`}
        >
          {isLoading ? 'Summarizing...' : 'Summarize PDF'}
        </button>

        {error && summary === null && (
          <p className="text-red-500 mt-4">{error}</p>
        )}

        {summary && (
          <div className="mt-6 p-4 border rounded bg-gray-50">
            <h3 className="text-lg font-semibold mb-2">Summary:</h3>
            <pre className="whitespace-pre-wrap text-sm">{summary}</pre>
          </div>
        )}
      </div>

    </main>
  );
}
