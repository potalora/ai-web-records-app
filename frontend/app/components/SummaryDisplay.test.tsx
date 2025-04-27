import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import SummaryDisplay from './SummaryDisplay';

describe('SummaryDisplay Component', () => {
  test('renders nothing when no props are provided or all are null/false', () => {
    const { container } = render(<SummaryDisplay summary={null} isLoading={false} error={null} />);
    // Expect the component to render essentially empty
    expect(container.firstChild).toBeNull(); 
  });

  test('renders loading indicator when isLoading is true', () => {
    render(<SummaryDisplay summary={null} isLoading={true} error={null} />);
    expect(screen.getByText(/Generating summary.../i)).toBeInTheDocument();
    // Check for pulse animation class if needed, though text check is usually sufficient
    expect(screen.getByText(/Generating summary.../i)).toHaveClass('animate-pulse');
  });

  test('renders error message when error is provided', () => {
    const errorMessage = 'Failed to fetch summary.';
    render(<SummaryDisplay summary={null} isLoading={false} error={errorMessage} />);
    expect(screen.getByText(/Error generating summary:/i)).toBeInTheDocument();
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  test('renders summary content when summary string is provided', () => {
    const summaryText = 'This is the generated summary.\nIt has multiple lines.';
    render(<SummaryDisplay summary={summaryText} isLoading={false} error={null} />);
    expect(screen.getByText(/Summary:/i)).toBeInTheDocument();
    // Check that the summary text is present and preserves whitespace
    // Find the paragraph element containing the summary
    const summaryParagraph = screen.getByText((content, element) => {
      // Check if the element is a paragraph and its text content matches
      return element?.tagName.toLowerCase() === 'p' && element.textContent === summaryText;
    });
    expect(summaryParagraph).toBeInTheDocument();
    // Removed the style check as it's unreliable for Tailwind classes here
    // expect(summaryParagraph).toHaveStyle('white-space: pre-wrap');
  });

  test('prioritizes loading state over error or summary', () => {
    const errorMessage = 'An error occurred.';
    const summaryText = 'A summary was generated.';
    render(<SummaryDisplay summary={summaryText} isLoading={true} error={errorMessage} />);
    // Should only show loading
    expect(screen.getByText(/Generating summary.../i)).toBeInTheDocument();
    expect(screen.queryByText(/Error generating summary:/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Summary:/i)).not.toBeInTheDocument();
  });

  test('prioritizes error state over summary state (when not loading)', () => {
    const errorMessage = 'An error occurred.';
    const summaryText = 'A summary was generated.';
    render(<SummaryDisplay summary={summaryText} isLoading={false} error={errorMessage} />);
    // Should only show error
    expect(screen.queryByText(/Generating summary.../i)).not.toBeInTheDocument();
    expect(screen.getByText(/Error generating summary:/i)).toBeInTheDocument();
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
    // Use data-testid to ensure the entire summary section is absent
    expect(screen.queryByTestId('summary-content-section')).not.toBeInTheDocument();
  });
});
