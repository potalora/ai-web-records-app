import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import axios from 'axios';
import ProviderModelSelector from './ProviderModelSelector';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock data
const mockModelsData = {
  openai: ['gpt-4', 'gpt-3.5-turbo'],
  google: ['gemini-pro', 'gemini-flash'],
  anthropic: ['claude-3-sonnet', 'claude-3-opus'],
};

describe('ProviderModelSelector Component', () => {
  let mockOnProviderChange: jest.Mock;
  let mockOnModelChange: jest.Mock;
  let mockSetLoadingError: jest.Mock;

  beforeEach(() => {
    // Reset mocks only
    mockedAxios.get.mockReset();
    mockOnProviderChange = jest.fn();
    mockOnModelChange = jest.fn();
    mockSetLoadingError = jest.fn();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('renders loading state initially then fetches models', async () => {
    // Setup mock specifically for this test BEFORE render
    mockedAxios.get.mockResolvedValue({ data: mockModelsData });

    render( // No act needed for initial synchronous render
        <ProviderModelSelector
            selectedProvider="openai"
            selectedModel="gpt-4"
            onProviderChange={mockOnProviderChange}
            onModelChange={mockOnModelChange}
            setLoadingError={mockSetLoadingError}
        />
    );

    // 2. Wait for async fetch and subsequent render update to finish
    await waitFor(() => {
        expect(screen.queryByText(/Loading available models.../i)).not.toBeInTheDocument();
    });

    // 3. Assert final state after load
    expect(screen.getByLabelText(/openai/i)).toBeChecked();
    const selectElement = screen.getByRole('combobox');
    expect(selectElement).toBeInTheDocument();
    expect(selectElement).toHaveValue('gpt-4');
    expect(screen.getByRole('option', { name: 'gpt-4' })).toBeInTheDocument();
  });

  test('handles API error during model fetch and calls setLoadingError', async () => {
    // Setup error mock specifically for this test BEFORE render
    const networkError = new Error('Network Error');
    mockedAxios.get.mockRejectedValue(networkError);

    render( // No act needed for initial sync render
      <ProviderModelSelector
        selectedProvider="openai"
        selectedModel="gpt-4"
        onProviderChange={mockOnProviderChange}
        onModelChange={mockOnModelChange}
        setLoadingError={mockSetLoadingError}
      />
    );

    // Check initial loading state
    expect(screen.getByText(/Loading available models.../i)).toBeInTheDocument();

    // Wait for the error message to appear due to the failed fetch
    await waitFor(() => {
        expect(screen.getByText(/Error: Failed to load models. Is backend running?/i)).toBeInTheDocument();
    });

    // Assert error state
    expect(screen.queryByText(/Loading available models.../i)).not.toBeInTheDocument();
    expect(mockSetLoadingError).toHaveBeenCalledWith('Failed to load models. Is backend running?');
    // Allow multiple calls due to potential strict mode double effects
    expect(mockSetLoadingError.mock.calls.length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByRole('combobox')).not.toBeInTheDocument();
  });


  test('changes provider and model correctly', async () => {
    // Setup success mock specifically for this test
    mockedAxios.get.mockResolvedValue({ data: mockModelsData });

    // Initial Render
    const { rerender } = render(
      <ProviderModelSelector
        selectedProvider="openai"
        selectedModel="gpt-4"
        onProviderChange={mockOnProviderChange}
        onModelChange={mockOnModelChange}
        setLoadingError={mockSetLoadingError}
      />
    );

    // Wait for initial load to complete
    await waitFor(() => {
      expect(screen.queryByText(/Loading available models.../i)).not.toBeInTheDocument();
      expect(screen.getByRole('combobox')).toHaveValue('gpt-4');
    });

    // --- Change Provider ---
    // User clicks 'google' radio -> triggers state update
    await act(async () => {
        fireEvent.click(screen.getByLabelText(/google/i));
    });

    // Assert mock was called due to click
    expect(mockOnProviderChange).toHaveBeenCalledTimes(1);
    expect(mockOnProviderChange).toHaveBeenCalledWith('google');

    // Parent component updates state -> triggers rerender
    // No act needed for rerender itself if no new async ops are triggered by it directly
     rerender(
        <ProviderModelSelector
            selectedProvider="google" // New provider from parent
            selectedModel="gemini-pro" // New model from parent
            onProviderChange={mockOnProviderChange}
            onModelChange={mockOnModelChange}
            setLoadingError={mockSetLoadingError}
        />
    );


    // Wait for UI to update based on new props
    await waitFor(() => {
        expect(screen.getByLabelText(/google/i)).toBeChecked();
        const selectElement = screen.getByRole('combobox');
        expect(selectElement).toHaveValue('gemini-pro');
        expect(screen.getByRole('option', { name: 'gemini-pro' })).toBeInTheDocument();
        expect(screen.getByRole('option', { name: 'gemini-flash'})).toBeInTheDocument();
        expect(screen.queryByRole('option', { name: 'gpt-4' })).not.toBeInTheDocument();
    });

     // --- Change Model ---
     // User selects different model -> triggers state update
    await act(async () => {
         fireEvent.change(screen.getByRole('combobox'), { target: { value: 'gemini-flash' } });
    });

    // Assert mock was called due to change event
    expect(mockOnModelChange).toHaveBeenCalledTimes(1); // Should only be called by this user action
    expect(mockOnModelChange).toHaveBeenCalledWith('gemini-flash');

  });

  test('selects a different model within the same provider and calls onModelChange', async () => {
     // Setup success mock
     mockedAxios.get.mockResolvedValue({ data: mockModelsData });

     render(
       <ProviderModelSelector
         selectedProvider="openai"
         selectedModel="gpt-4"
         onProviderChange={mockOnProviderChange}
         onModelChange={mockOnModelChange}
         setLoadingError={mockSetLoadingError}
       />
     );

      // Wait for initial load
      await waitFor(() => {
         expect(screen.queryByText(/Loading available models.../i)).not.toBeInTheDocument();
         expect(screen.getByRole('combobox')).toBeInTheDocument();
      });

      // User changes selection -> triggers state update
      await act(async () => {
         fireEvent.change(screen.getByRole('combobox'), { target: { value: 'gpt-3.5-turbo' } });
      });

     // Assert mock was called
     expect(mockOnModelChange).toHaveBeenCalledTimes(1);
     expect(mockOnModelChange).toHaveBeenCalledWith('gpt-3.5-turbo');
     expect(mockOnProviderChange).not.toHaveBeenCalled();
   });

});
