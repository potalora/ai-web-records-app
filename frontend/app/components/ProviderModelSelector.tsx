'use client';

import React, { useState, useEffect, ChangeEvent } from 'react';
import axios from 'axios';

// Define the structure for the models data fetched from the API
interface AvailableModels {
  [provider: string]: string[];
}

// Define allowed provider strings using a type for better safety
type Provider = 'openai' | 'google' | 'anthropic';

// Define the component's props
interface ProviderModelSelectorProps {
  selectedProvider: Provider;
  selectedModel: string; // Parent must ensure this is valid for the provider
  onProviderChange: (provider: Provider) => void;
  onModelChange: (model: string) => void;
  setLoadingError: (error: string | null) => void; // Callback to inform parent of loading errors
}

const ProviderModelSelector: React.FC<ProviderModelSelectorProps> = ({ 
  selectedProvider, 
  selectedModel, 
  onProviderChange, 
  onModelChange, 
  setLoadingError 
}) => {
  const [availableModels, setAvailableModels] = useState<AvailableModels>({});
  const [isLoadingModels, setIsLoadingModels] = useState<boolean>(true);
  const [internalLoadingError, setInternalLoadingError] = useState<string | null>(null); // Internal state for loading error

  // Effect to fetch available models from the backend API on component mount
  useEffect(() => {
    let isMounted = true; // Prevent state update on unmounted component
    const fetchModels = async () => {
      setIsLoadingModels(true);
      setInternalLoadingError(null);
      setLoadingError(null); 
      try {
        const response = await axios.get('/api/proxy?target=http://localhost:8000/models/');
        console.log('Fetched models data:', response.data); 
        if (isMounted) { // Check if component is still mounted
            if (response.data && typeof response.data === 'object') {
            setAvailableModels(response.data);
            } else {
            console.error('Received non-object data for models:', response.data);
            const errorMsg = 'Failed to load models: Invalid format received.';
            setInternalLoadingError(errorMsg);
            setLoadingError(errorMsg);
            setAvailableModels({});
            }
        }
      } catch (err) {
         if (isMounted) { // Check if component is still mounted
            console.error('Error fetching available models:', err);
            const errorMsg = 'Failed to load models. Is backend running?';
            setInternalLoadingError(errorMsg);
            setLoadingError(errorMsg);
            setAvailableModels({});
         }
      } finally {
        if (isMounted) { // Check if component is still mounted
            setIsLoadingModels(false);
        }
      }
    };

    fetchModels();

    return () => { // Cleanup function
        isMounted = false;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Run only on mount

  // Handle provider radio button change
  const handleProviderRadioChange = (event: ChangeEvent<HTMLInputElement>) => {
    // Parent component will be responsible for potentially updating selectedModel
    onProviderChange(event.target.value as Provider);
  };

  // Handle model dropdown selection change
  const handleModelSelectChange = (event: ChangeEvent<HTMLSelectElement>) => {
    onModelChange(event.target.value);
  };

  // Use a defined list for rendering radios to ensure order and existence
  const providersToDisplay: Provider[] = ['openai', 'google', 'anthropic'];
  // Derive models directly from state/props for rendering
  const modelsForCurrentProvider = availableModels[selectedProvider] || [];

  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700 mb-2">
        Choose Summarization Provider & Model
      </label>

      {isLoadingModels ? (
        <p className="text-sm text-gray-500 animate-pulse">Loading available models...</p>
      ) : ( 
        <div> 
          <div className="flex items-center space-x-4 mb-3">
            {providersToDisplay.map((provider) => (
              <label key={provider} className="flex items-center space-x-1 cursor-pointer">
                <input
                  type="radio"
                  name="provider"
                  value={provider}
                  checked={selectedProvider === provider}
                  onChange={handleProviderRadioChange}
                  className="form-radio h-4 w-4 text-blue-600 transition duration-150 ease-in-out"
                  disabled={isLoadingModels || !!internalLoadingError} // Disable radios if loading/error
                />
                <span className="text-sm capitalize">{provider}</span>
              </label>
            ))}
          </div>

          {/* Conditional Rendering for Model Selector */}
          {!isLoadingModels && !internalLoadingError && modelsForCurrentProvider.length > 0 && (
            <select
              name="model"
              value={selectedModel} // Relies on parent providing a valid value
              onChange={handleModelSelectChange}
              className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md shadow-sm"
              disabled={isLoadingModels || !!internalLoadingError} 
            >
              {modelsForCurrentProvider.map((modelName) => (
                <option key={modelName} value={modelName}>
                  {modelName}
                </option>
              ))}
            </select>
          )}

          {/* Message when no models are available for the selected provider */}
          {!isLoadingModels && !internalLoadingError && modelsForCurrentProvider.length === 0 && (
            <p className="text-sm text-gray-500">
              No models available for {selectedProvider}.
            </p>
          )}

          {/* Message when loading fails */}
          {internalLoadingError && (
             <p className="text-sm text-red-600 mt-1">Error: {internalLoadingError}</p>
          )}
          
        </div> 
      )}
    </div>
  );
};

export default ProviderModelSelector;
