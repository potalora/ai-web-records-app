'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { 
  Search, 
  AlertCircle, 
  ExternalLink, 
  BookOpen, 
  Calendar,
  Users,
  Loader2
} from 'lucide-react';
import apiClient, { PubMedResult } from '@/lib/api-client';
import { useApi } from '@/hooks/use-api';

export function PubMedSearch() {
  const [query, setQuery] = useState('');
  const [maxResults, setMaxResults] = useState(10);

  const {
    data: searchResults,
    loading: searching,
    execute: searchPubMed,
    error: searchError,
    reset
  } = useApi(apiClient.searchPubMed);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!query.trim()) {
      return;
    }

    try {
      await searchPubMed({
        query: query.trim(),
        max_results: maxResults
      });
    } catch (error) {
      console.error('Search failed:', error);
    }
  };

  const handleClearSearch = () => {
    setQuery('');
    reset();
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            PubMed Medical Evidence Search
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="space-y-4">
            <div>
              <Label htmlFor="search-query">Search Terms</Label>
              <Input
                id="search-query"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter medical terms, conditions, treatments..."
                className="mt-2"
                disabled={searching}
              />
              <p className="text-xs text-muted-foreground mt-1">
                Example: "hypertension treatment", "vitamin D deficiency", "diabetes type 2"
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="max-results">Max Results</Label>
                <Input
                  id="max-results"
                  type="number"
                  min="1"
                  max="50"
                  value={maxResults}
                  onChange={(e) => setMaxResults(parseInt(e.target.value) || 10)}
                  className="mt-2"
                  disabled={searching}
                />
              </div>
            </div>

            <div className="flex gap-2">
              <Button type="submit" disabled={!query.trim() || searching}>
                {searching ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Searching...
                  </>
                ) : (
                  <>
                    <Search className="mr-2 h-4 w-4" />
                    Search PubMed
                  </>
                )}
              </Button>
              
              {searchResults && (
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={handleClearSearch}
                  disabled={searching}
                >
                  Clear Results
                </Button>
              )}
            </div>
          </form>

          {/* Error */}
          {searchError && (
            <Alert variant="destructive" className="mt-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Search failed: {searchError.detail}
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Search Results */}
      {searchResults && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <BookOpen className="h-5 w-5" />
                Search Results
              </div>
              <Badge variant="secondary">
                {searchResults.total_results} total results
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="text-sm text-muted-foreground mb-4">
                Query: <strong>"{searchResults.query}"</strong>
              </div>

              {searchResults.results.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  No results found for your search query.
                </div>
              ) : (
                <div className="space-y-4">
                  {searchResults.results.map((result: PubMedResult, index: number) => (
                    <div key={result.pmid} className="border rounded-lg p-4 hover:bg-slate-50">
                      <div className="space-y-3">
                        {/* Title */}
                        <h3 className="font-semibold text-lg leading-tight">
                          {result.title}
                        </h3>

                        {/* Metadata */}
                        <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
                          <div className="flex items-center gap-1">
                            <Users className="h-3 w-3" />
                            <span>{result.authors.join(', ')}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            <span>{result.publication_date}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <BookOpen className="h-3 w-3" />
                            <span>{result.journal}</span>
                          </div>
                        </div>

                        {/* Abstract */}
                        {result.abstract && (
                          <div className="text-sm leading-relaxed">
                            <p className="line-clamp-3">{result.abstract}</p>
                          </div>
                        )}

                        {/* Links */}
                        <div className="flex items-center gap-2 pt-2">
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => window.open(result.url, '_blank')}
                          >
                            <ExternalLink className="mr-1 h-3 w-3" />
                            View on PubMed
                          </Button>
                          
                          {result.doi && (
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => window.open(`https://doi.org/${result.doi}`, '_blank')}
                            >
                              DOI: {result.doi}
                            </Button>
                          )}
                          
                          <Badge variant="outline" className="ml-auto">
                            PMID: {result.pmid}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Show more note */}
              {searchResults.total_results > searchResults.results.length && (
                <div className="text-center text-sm text-muted-foreground pt-4 border-t">
                  Showing {searchResults.results.length} of {searchResults.total_results} results.
                  Increase "Max Results" to see more.
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}