import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { createTheme } from '@mui/material/styles';
import { act } from 'react-dom/test-utils';
import MobileSearchBar from './MobileSearchBar';

/**
 * MobileSearchBar Component Tests
 *
 * Tests the mobile-optimized search bar component including:
 * - Rendering with various props
 * - Auto-focus behavior on mobile
 * - Voice search functionality
 * - Debounced search
 * - Clear button functionality
 * - Input change handling
 */

const theme = createTheme();

const renderWithTheme = (component: React.ReactElement) => {
  return render(<ThemeProvider theme={theme}>{component}</ThemeProvider>);
};

// Mock Speech Recognition API
const mockSpeechRecognition = vi.fn();

class MockSpeechRecognition {
  continuous = false;
  interimResults = true;
  lang = 'en-US';
  onresult: ((event: SpeechRecognitionEvent) => void) | null = null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null = null;
  onstart: ((event: Event) => void) | null = null;
  onend: ((event: Event) => void) | null = null;

  start() {
    // Simulate recognition start
    if (this.onstart) {
      this.onstart(new Event('start'));
    }
  }

  stop() {
    // Simulate recognition end
    if (this.onend) {
      this.onend(new Event('end'));
    }
  }

  abort() {
    // Simulate recognition abort
    if (this.onend) {
      this.onend(new Event('end'));
    }
  }
}

describe('MobileSearchBar', () => {
  beforeEach(() => {
    // Setup Speech Recognition mock
    (window as any).SpeechRecognition = MockSpeechRecognition;
    (window as any).webkitSpeechRecognition = MockSpeechRecognition;
  });

  afterEach(() => {
    vi.clearAllMocks();
    // Clean up timers
    vi.useRealTimers();
  });

  describe('Rendering', () => {
    it('should render search input correctly', () => {
      const handleChange = vi.fn();
      renderWithTheme(
        <MobileSearchBar value="" onChange={handleChange} />
      );

      const input = screen.getByRole('textbox');
      expect(input).toBeInTheDocument();
      expect(input).toHaveAttribute('placeholder', expect.any(String));
    });

    it('should render with custom placeholder', () => {
      const handleChange = vi.fn();
      renderWithTheme(
        <MobileSearchBar
          value=""
          onChange={handleChange}
          placeholder="Search candidates..."
        />
      );

      const input = screen.getByPlaceholderText('Search candidates...');
      expect(input).toBeInTheDocument();
    });

    it('should display current value', () => {
      const handleChange = vi.fn();
      renderWithTheme(
        <MobileSearchBar value="React Developer" onChange={handleChange} />
      );

      const input = screen.getByDisplayValue('React Developer');
      expect(input).toBeInTheDocument();
    });

    it('should render search icon', () => {
      const handleChange = vi.fn();
      const { container } = renderWithTheme(
        <MobileSearchBar value="" onChange={handleChange} />
      );

      const searchIcon = container.querySelector('[data-testid="SearchIcon"]');
      expect(searchIcon).toBeInTheDocument();
    });

    it('should render loading state', () => {
      const handleChange = vi.fn();
      renderWithTheme(
        <MobileSearchBar value="" onChange={handleChange} loading={true} />
      );

      // Should show circular progress instead of search icon when loading
      const progress = document.querySelector('.MuiCircularProgress-root');
      expect(progress).toBeInTheDocument();
    });
  });

  describe('Input Handling', () => {
    it('should call onChange when input changes', () => {
      const handleChange = vi.fn();
      renderWithTheme(
        <MobileSearchBar value="" onChange={handleChange} />
      );

      const input = screen.getByRole('textbox');
      fireEvent.change(input, { target: { value: 'React' } });

      expect(handleChange).toHaveBeenCalledWith('React');
    });

    it('should call onSearch when Enter key is pressed', () => {
      const handleChange = vi.fn();
      const handleSearch = vi.fn();
      renderWithTheme(
        <MobileSearchBar
          value="React"
          onChange={handleChange}
          onSearch={handleSearch}
        />
      );

      const input = screen.getByRole('textbox');
      fireEvent.keyPress(input, { key: 'Enter', code: 'Enter' });

      expect(handleSearch).toHaveBeenCalledWith('React');
    });

    it('should update input value correctly', () => {
      const handleChange = vi.fn();
      renderWithTheme(
        <MobileSearchBar value="" onChange={handleChange} />
      );

      const input = screen.getByRole('textbox') as HTMLInputElement;

      fireEvent.change(input, { target: { value: 'TypeScript' } });
      expect(handleChange).toHaveBeenCalledWith('TypeScript');
    });
  });

  describe('Clear Button', () => {
    it('should show clear button when value is present', () => {
      const handleChange = vi.fn();
      const { container } = renderWithTheme(
        <MobileSearchBar value="React" onChange={handleChange} />
      );

      const clearIcon = container.querySelector('[data-testid="CloseIcon"]');
      expect(clearIcon).toBeInTheDocument();
    });

    it('should not show clear button when value is empty', () => {
      const handleChange = vi.fn();
      const { container } = renderWithTheme(
        <MobileSearchBar value="" onChange={handleChange} />
      );

      const clearIcon = container.querySelector('[data-testid="CloseIcon"]');
      expect(clearIcon).not.toBeInTheDocument();
    });

    it('should clear input when clear button is clicked', () => {
      const handleChange = vi.fn();
      const { container } = renderWithTheme(
        <MobileSearchBar value="React Developer" onChange={handleChange} />
      );

      const clearButton = container.querySelector('[aria-label="Clear search"]');
      expect(clearButton).toBeInTheDocument();

      fireEvent.click(clearButton!);
      expect(handleChange).toHaveBeenCalledWith('');
    });
  });

  describe('Voice Search', () => {
    it('should render voice search button when supported', () => {
      const handleChange = vi.fn();
      const { container } = renderWithTheme(
        <MobileSearchBar value="" onChange={handleChange} showVoiceSearch={true} />
      );

      const micIcon = container.querySelector('[data-testid="MicIcon"]');
      expect(micIcon).toBeInTheDocument();
    });

    it('should not render voice search button when showVoiceSearch is false', () => {
      const handleChange = vi.fn();
      const { container } = renderWithTheme(
        <MobileSearchBar value="" onChange={handleChange} showVoiceSearch={false} />
      );

      const micIcon = container.querySelector('[data-testid="MicIcon"]');
      expect(micIcon).not.toBeInTheDocument();
    });

    it('should start voice recognition when mic button is clicked', async () => {
      const handleChange = vi.fn();
      const { container } = renderWithTheme(
        <MobileSearchBar value="" onChange={handleChange} showVoiceSearch={true} />
      );

      const micButton = container.querySelector('[aria-label="Voice search"]');
      expect(micButton).toBeInTheDocument();

      await act(async () => {
        fireEvent.click(micButton!);
      });

      // After clicking, the button should show "Stop listening"
      const stopButton = container.querySelector('[aria-label="Stop listening"]');
      expect(stopButton).toBeInTheDocument();
    });
  });

  describe('Debounced Search', () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });

    it('should debounce search when debounceMs is set', () => {
      const handleChange = vi.fn();
      const handleSearch = vi.fn();
      renderWithTheme(
        <MobileSearchBar
          value=""
          onChange={handleChange}
          onSearch={handleSearch}
          debounceMs={500}
        />
      );

      const input = screen.getByRole('textbox');

      fireEvent.change(input, { target: { value: 'React' } });

      // Should not call search immediately
      expect(handleSearch).not.toHaveBeenCalled();

      // Fast-forward 500ms
      act(() => {
        vi.advanceTimersByTime(500);
      });

      expect(handleSearch).toHaveBeenCalledWith('React');
    });

    it('should trigger search immediately when debounceMs is 0', () => {
      const handleChange = vi.fn();
      const handleSearch = vi.fn();
      renderWithTheme(
        <MobileSearchBar
          value=""
          onChange={handleChange}
          onSearch={handleSearch}
          debounceMs={0}
        />
      );

      const input = screen.getByRole('textbox');

      fireEvent.change(input, { target: { value: 'React' } });

      expect(handleSearch).toHaveBeenCalledWith('React');
    });

    it('should not trigger onSearch when not provided', () => {
      vi.useFakeTimers();
      const handleChange = vi.fn();
      renderWithTheme(
        <MobileSearchBar value="" onChange={handleChange} debounceMs={300} />
      );

      const input = screen.getByRole('textbox');

      fireEvent.change(input, { target: { value: 'React' } });

      act(() => {
        vi.advanceTimersByTime(300);
      });

      // Should not throw error
      expect(input).toHaveValue('React');
    });
  });

  describe('Accessibility', () => {
    it('should have correct aria labels', () => {
      const handleChange = vi.fn();
      const { container } = renderWithTheme(
        <MobileSearchBar value="React" onChange={handleChange} />
      );

      const searchInput = screen.getByRole('textbox');
      expect(searchInput).toBeInTheDocument();

      const clearButton = container.querySelector('[aria-label="Clear search"]');
      expect(clearButton).toBeInTheDocument();

      const voiceButton = container.querySelector('[aria-label="Voice search"]');
      expect(voiceButton).toBeInTheDocument();
    });

    it('should have inputMode set to search', () => {
      const handleChange = vi.fn();
      renderWithTheme(
        <MobileSearchBar value="" onChange={handleChange} />
      );

      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('inputMode', 'search');
    });

    it('should be keyboard accessible', () => {
      const handleChange = vi.fn();
      const handleSearch = vi.fn();
      renderWithTheme(
        <MobileSearchBar
          value="React"
          onChange={handleChange}
          onSearch={handleSearch}
        />
      );

      const input = screen.getByRole('textbox');

      // Tab to focus
      fireEvent.focus(input);

      // Type
      fireEvent.change(input, { target: { value: 'React Developer' } });

      // Press Enter
      fireEvent.keyPress(input, { key: 'Enter', code: 'Enter' });

      expect(handleSearch).toHaveBeenCalledWith('React Developer');
    });
  });

  describe('Styling', () => {
    it('should apply custom sx styles', () => {
      const handleChange = vi.fn();
      const { container } = renderWithTheme(
        <MobileSearchBar
          value=""
          onChange={handleChange}
          sx={{ bgcolor: 'primary.main' }}
        />
      );

      const paper = container.querySelector('.MuiPaper-root');
      expect(paper).toHaveStyle({ backgroundColor: 'rgb(25, 118, 210)' });
    });

    it('should pass TextFieldProps correctly', () => {
      const handleChange = vi.fn();
      renderWithTheme(
        <MobileSearchBar
          value=""
          onChange={handleChange}
          TextFieldProps={{
            variant: 'filled',
            size: 'small',
          }}
        />
      );

      const input = screen.getByRole('textbox');
      expect(input).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty value correctly', () => {
      const handleChange = vi.fn();
      renderWithTheme(
        <MobileSearchBar value="" onChange={handleChange} />
      );

      const input = screen.getByRole('textbox');
      expect(input).toHaveValue('');
    });

    it('should handle long input values', () => {
      const handleChange = vi.fn();
      const longValue = 'A'.repeat(1000);
      renderWithTheme(
        <MobileSearchBar value={longValue} onChange={handleChange} />
      );

      const input = screen.getByDisplayValue(longValue);
      expect(input).toBeInTheDocument();
    });

    it('should handle special characters in input', () => {
      const handleChange = vi.fn();
      const specialValue = 'React, TypeScript; Node.js! @#$%';
      renderWithTheme(
        <MobileSearchBar value={specialValue} onChange={handleChange} />
      );

      const input = screen.getByDisplayValue(specialValue);
      expect(input).toBeInTheDocument();
    });

    it('should not crash with null onSearch', () => {
      const handleChange = vi.fn();
      expect(() => {
        renderWithTheme(
          <MobileSearchBar
            value=""
            onChange={handleChange}
            onSearch={undefined as any}
          />
        );
      }).not.toThrow();
    });

    it('should handle rapid input changes with debounce', () => {
      vi.useFakeTimers();
      const handleChange = vi.fn();
      const handleSearch = vi.fn();
      renderWithTheme(
        <MobileSearchBar
          value=""
          onChange={handleChange}
          onSearch={handleSearch}
          debounceMs={300}
        />
      );

      const input = screen.getByRole('textbox');

      // Rapid changes
      fireEvent.change(input, { target: { value: 'R' } });
      fireEvent.change(input, { target: { value: 'Re' } });
      fireEvent.change(input, { target: { value: 'Rea' } });
      fireEvent.change(input, { target: { value: 'Reac' } });
      fireEvent.change(input, { target: { value: 'React' } });

      // Only last value should trigger search after debounce
      act(() => {
        vi.advanceTimersByTime(300);
      });

      expect(handleSearch).toHaveBeenCalledTimes(1);
      expect(handleSearch).toHaveBeenCalledWith('React');
    });
  });
});
