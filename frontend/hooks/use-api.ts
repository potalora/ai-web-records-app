'use client';

import { useState, useCallback } from 'react';
import { ApiError } from '@/lib/api-client';

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: ApiError | null;
}

interface UseApiResult<T> extends UseApiState<T> {
  execute: (...args: any[]) => Promise<T>;
  reset: () => void;
}

/**
 * Hook for handling API operations with loading, error, and success states
 */
export function useApi<T>(
  apiFunction: (...args: any[]) => Promise<T>
): UseApiResult<T> {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: false,
    error: null,
  });

  const execute = useCallback(
    async (...args: any[]): Promise<T> => {
      setState(prev => ({ ...prev, loading: true, error: null }));

      try {
        const result = await apiFunction(...args);
        setState({
          data: result,
          loading: false,
          error: null,
        });
        return result;
      } catch (error) {
        const apiError = error as ApiError;
        setState({
          data: null,
          loading: false,
          error: apiError,
        });
        throw error;
      }
    },
    [apiFunction]
  );

  const reset = useCallback(() => {
    setState({
      data: null,
      loading: false,
      error: null,
    });
  }, []);

  return {
    ...state,
    execute,
    reset,
  };
}

/**
 * Hook for handling file uploads with progress
 */
export function useFileUpload<T>(
  uploadFunction: (file: File, ...args: any[]) => Promise<T>
) {
  const [progress, setProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [result, setResult] = useState<T | null>(null);

  const upload = useCallback(
    async (file: File, ...args: any[]): Promise<T> => {
      setUploading(true);
      setProgress(0);
      setError(null);
      setResult(null);

      try {
        // Simulate progress for user feedback
        const progressInterval = setInterval(() => {
          setProgress(prev => {
            if (prev >= 90) {
              clearInterval(progressInterval);
              return prev;
            }
            return prev + 10;
          });
        }, 200);

        const uploadResult = await uploadFunction(file, ...args);

        clearInterval(progressInterval);
        setProgress(100);
        setResult(uploadResult);
        
        // Keep 100% progress visible briefly
        setTimeout(() => {
          setUploading(false);
          setProgress(0);
        }, 1000);

        return uploadResult;
      } catch (error) {
        const apiError = error as ApiError;
        setError(apiError);
        setUploading(false);
        setProgress(0);
        throw error;
      }
    },
    [uploadFunction]
  );

  const reset = useCallback(() => {
    setProgress(0);
    setUploading(false);
    setError(null);
    setResult(null);
  }, []);

  return {
    upload,
    uploading,
    progress,
    error,
    result,
    reset,
  };
}