'use client';

import React from 'react';

interface SummaryDisplayProps {
  summary: string | null;
  isLoading: boolean;
  error: string | null;
}

const SummaryDisplay: React.FC<SummaryDisplayProps> = ({ summary, isLoading, error }) => {
  if (isLoading) {
    return (
      <div className="mt-4 p-4 border border-gray-200 rounded-md bg-white shadow-sm flex items-center justify-center">
        <p className="text-gray-600 animate-pulse">Generating summary...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mt-4 p-4 border border-red-200 rounded-md bg-red-50 shadow-sm">
        <p className="text-red-700 font-medium">Error generating summary:</p>
        <p className="text-red-600 text-sm mt-1">{error}</p>
      </div>
    );
  }

  // Only render summary if not loading and NO error
  if (summary && !error) {
    return (
      <div 
        className="mt-4 p-4 border border-gray-200 rounded-md bg-white shadow-sm"
        data-testid="summary-content-section"
      >
        <h3 className="text-lg font-semibold mb-2 text-gray-800">Summary:</h3>
        <p className="text-gray-700 whitespace-pre-wrap">{summary}</p>
      </div>
    );
  }

  // Render nothing if no relevant props are provided
  return null;
};

export default SummaryDisplay;
