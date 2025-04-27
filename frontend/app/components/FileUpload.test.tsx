import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import FileUpload from './FileUpload';

describe('FileUpload Component', () => {
  const mockOnFileChange = jest.fn();

  beforeEach(() => {
    // Reset mocks before each test
    mockOnFileChange.mockClear();
  });

  test('renders the file input', () => {
    render(<FileUpload onFileChange={mockOnFileChange} />);
    
    const inputElement = screen.getByLabelText(/Upload Document/i);
    expect(inputElement).toBeInTheDocument();
    expect(inputElement).toHaveAttribute('type', 'file');
  });

  test('accepts the default file type (pdf)', () => {
    render(<FileUpload onFileChange={mockOnFileChange} />);
    const inputElement = screen.getByLabelText(/Upload Document/i);
    expect(inputElement).toHaveAttribute('accept', 'application/pdf');
  });

  test('accepts a custom file type', () => {
    const customAccept = 'image/png,image/jpeg';
    render(<FileUpload onFileChange={mockOnFileChange} acceptedFileType={customAccept} />);
    const inputElement = screen.getByLabelText(/Upload Document/i);
    expect(inputElement).toHaveAttribute('accept', customAccept);
  });

  test('calls onFileChange with the selected file', () => {
    render(<FileUpload onFileChange={mockOnFileChange} />);
    const inputElement = screen.getByLabelText(/Upload Document/i);

    const file = new File(['dummy content'], 'test.pdf', { type: 'application/pdf' });

    // Simulate file selection
    fireEvent.change(inputElement, {
      target: { files: [file] },
    });

    expect(mockOnFileChange).toHaveBeenCalledTimes(1);
    expect(mockOnFileChange).toHaveBeenCalledWith(file);
  });

  test('calls onFileChange with null if no file is selected', () => {
    render(<FileUpload onFileChange={mockOnFileChange} />);
    const inputElement = screen.getByLabelText(/Upload Document/i);

    // Simulate clearing the file input (or selecting nothing)
    fireEvent.change(inputElement, {
      target: { files: [] }, // Empty array
    });

    expect(mockOnFileChange).toHaveBeenCalledTimes(1);
    expect(mockOnFileChange).toHaveBeenCalledWith(null);
  });
});
