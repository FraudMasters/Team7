import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  TextField,
  IconButton,
  InputAdornment,
  Paper,
  CircularProgress,
  Tooltip,
  useTheme,
  useMediaQuery,
  SxProps,
  Theme,
} from '@mui/material';
import {
  Search as SearchIcon,
  Mic as MicIcon,
  MicOff as MicOffIcon,
  Close as ClearIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';

/**
 * Voice recognition state
 */
interface VoiceRecognitionState {
  isListening: boolean;
  isSupported: boolean;
  transcript: string;
  interimTranscript: string;
}

/**
 * Props for MobileSearchBar component
 */
export interface MobileSearchBarProps {
  /**
   * Current search query value
   */
  value: string;

  /**
   * Callback when search query changes
   */
  onChange: (query: string) => void;

  /**
   * Callback when search is submitted (Enter key or search button)
   */
  onSearch?: (query: string) => void;

  /**
   * Placeholder text for the search input
   */
  placeholder?: string;

  /**
   * Whether to show the voice search button
   * @default true
   */
  showVoiceSearch?: boolean;

  /**
   * Whether to auto-focus the input on mount
   * @default true on mobile, false on desktop
   */
  autoFocus?: boolean;

  /**
   * Delay in milliseconds before triggering search after input stops
   * Use 0 to disable debounce (search on every keystroke)
   * @default 300
   */
  debounceMs?: number;

  /**
   * Whether the search is currently loading
   */
  loading?: boolean;

  /**
   * Custom styles for the component
   */
  sx?: SxProps<Theme>;

  /**
   * Additional props to pass to the TextField
   */
  TextFieldProps?: React.ComponentProps<typeof TextField>;
}

/**
 * MobileSearchBar Component
 *
 * A mobile-optimized search bar component with the following features:
 *
 * - **Auto-focus**: Automatically focuses the input field on mobile devices
 * - **Voice Search**: Built-in voice recognition using Web Speech API
 * - **Debounced Search**: Configurable delay to avoid excessive search queries
 * - **Keyboard Optimization**: Uses inputMode="search" for better mobile keyboard
 * - **Clear Button**: Quickly clear the search query
 * - **Real-time Updates**: Optional debounced search as user types
 *
 * @module components/MobileSearchBar
 *
 * @example
 * ```tsx
 * function SearchPage() {
 *   const [query, setQuery] = useState('');
 *   const { isMobile } = useBreakpoints();
 *
 *   const handleSearch = useCallback((searchQuery: string) => {
 *     // Perform search
 *     console.log('Searching for:', searchQuery);
 *   }, []);
 *
 *   return (
 *     <MobileSearchBar
 *       value={query}
 *       onChange={setQuery}
 *       onSearch={handleSearch}
 *       placeholder="Search candidates..."
 *       autoFocus={isMobile}
 *     />
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * // With debounced real-time search
 * function CandidateSearch() {
 *   const [query, setQuery] = useState('');
 *
 *   useEffect(() => {
 *     if (query.length >= 2) {
 *       // Trigger search automatically
 *       searchCandidates(query);
 *     }
 *   }, [query]);
 *
 *   return (
 *     <MobileSearchBar
 *       value={query}
 *       onChange={setQuery}
 *       placeholder="Search by name, skills, or keywords..."
 *       debounceMs={500}
 *     />
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * // Without voice search and custom styling
 * function SimpleSearch() {
 *   const [query, setQuery] = useState('');
 *
 *   return (
 *     <MobileSearchBar
 *       value={query}
 *       onChange={setQuery}
 *       showVoiceSearch={false}
 *       sx={{
 *         bgcolor: 'primary.main',
 *         '& .MuiInputBase-input': {
 *           color: 'white',
 *         },
 *       }}
 *     />
 *   );
 * }
 * ```
 */
const MobileSearchBar: React.FC<MobileSearchBarProps> = ({
  value,
  onChange,
  onSearch,
  placeholder,
  showVoiceSearch = true,
  autoFocus,
  debounceMs = 300,
  loading = false,
  sx,
  TextFieldProps = {},
}) => {
  const { t } = useTranslation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Refs
  const inputRef = useRef<HTMLInputElement>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const debounceTimerRef = useRef<number | null>(null);

  // State
  const [voiceState, setVoiceState] = useState<VoiceRecognitionState>({
    isListening: false,
    isSupported: false,
    transcript: '',
    interimTranscript: '',
  });

  // Auto-focus logic
  const shouldAutoFocus = autoFocus !== undefined ? autoFocus : isMobile;

  useEffect(() => {
    if (shouldAutoFocus && inputRef.current) {
      // Small delay to ensure component is mounted
      const timer = setTimeout(() => {
        inputRef.current?.focus();
      }, 100);

      return () => clearTimeout(timer);
    }
  }, [shouldAutoFocus]);

  // Check for voice recognition support
  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (SpeechRecognition) {
      setVoiceState((prev) => ({ ...prev, isSupported: true }));

      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onstart = () => {
        setVoiceState((prev) => ({ ...prev, isListening: true, interimTranscript: '' }));
      };

      recognition.onresult = (event: SpeechRecognitionEvent) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }

        if (finalTranscript) {
          setVoiceState((prev) => ({
            ...prev,
            transcript: finalTranscript,
            interimTranscript: '',
          }));
          onChange(finalTranscript);
        } else {
          setVoiceState((prev) => ({ ...prev, interimTranscript }));
        }
      };

      recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
        console.error('Voice recognition error:', event.error);
        setVoiceState((prev) => ({
          ...prev,
          isListening: false,
          interimTranscript: '',
        }));
      };

      recognition.onend = () => {
        setVoiceState((prev) => ({
          ...prev,
          isListening: false,
          interimTranscript: '',
        }));
      };

      recognitionRef.current = recognition;
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, [onChange]);

  // Debounced search
  useEffect(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    if (onSearch && debounceMs > 0) {
      debounceTimerRef.current = window.setTimeout(() => {
        onSearch(value);
      }, debounceMs);

      return () => {
        if (debounceTimerRef.current) {
          clearTimeout(debounceTimerRef.current);
        }
      };
    }
  }, [value, onSearch, debounceMs]);

  // Handle input change
  const handleChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = event.target.value;
      onChange(newValue);

      // If debounce is disabled, trigger search immediately
      if (onSearch && debounceMs === 0) {
        onSearch(newValue);
      }
    },
    [onChange, onSearch, debounceMs]
  );

  // Handle key press
  const handleKeyPress = useCallback(
    (event: React.KeyboardEvent<HTMLInputElement>) => {
      if (event.key === 'Enter' && onSearch) {
        onSearch(value);
        inputRef.current?.blur();
      }
    },
    [onSearch, value]
  );

  // Handle clear
  const handleClear = useCallback(() => {
    onChange('');
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, [onChange]);

  // Handle voice search toggle
  const handleVoiceSearch = useCallback(() => {
    if (!recognitionRef.current || !voiceState.isSupported) {
      return;
    }

    if (voiceState.isListening) {
      recognitionRef.current.stop();
    } else {
      recognitionRef.current.start();
    }
  }, [voiceState.isListening, voiceState.isSupported]);

  // Display text for voice search
  const displayValue = voiceState.isListening && voiceState.interimTranscript
    ? voiceState.interimTranscript
    : value;

  return (
    <Paper
      elevation={isMobile ? 0 : 1}
      sx={{
        position: 'relative',
        borderRadius: 2,
        overflow: 'hidden',
        ...sx,
      }}
    >
      <TextField
        inputRef={inputRef}
        fullWidth
        value={displayValue}
        onChange={handleChange}
        onKeyPress={handleKeyPress}
        placeholder={placeholder || t('mobileSearchBar.placeholder')}
        inputMode="search"
        autoComplete="off"
        autoFocus={false}
        sx={{
          '& .MuiInputBase-root': {
            pr: 1,
          },
          '& .MuiInputBase-input': {
            fontSize: isMobile ? '1rem' : '0.875rem',
            py: isMobile ? 1.5 : 1,
          },
        }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              {loading ? (
                <CircularProgress size={20} />
              ) : (
                <SearchIcon color={value ? 'primary' : 'action'} />
              )}
            </InputAdornment>
          ),
          endAdornment: (
            <InputAdornment position="end">
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                {showVoiceSearch && voiceState.isSupported && (
                  <Tooltip
                    title={voiceState.isListening ? t('mobileSearchBar.stopListening') : t('mobileSearchBar.voiceSearch')}
                  >
                    <IconButton
                      size="small"
                      onClick={handleVoiceSearch}
                      color={voiceState.isListening ? 'error' : 'default'}
                      aria-label={voiceState.isListening ? t('mobileSearchBar.stopListening') : t('mobileSearchBar.voiceSearch')}
                      sx={{
                        bgcolor: voiceState.isListening ? 'error.main' : 'action.hover',
                        color: voiceState.isListening ? 'white' : 'text.primary',
                        '&:hover': {
                          bgcolor: voiceState.isListening ? 'error.dark' : 'action.selected',
                        },
                      }}
                    >
                      {voiceState.isListening ? <MicOffIcon /> : <MicIcon />}
                    </IconButton>
                  </Tooltip>
                )}

                {value && !voiceState.isListening && (
                  <Tooltip title={t('mobileSearchBar.clear')}>
                    <IconButton
                      size="small"
                      onClick={handleClear}
                      aria-label={t('mobileSearchBar.clear')}
                    >
                      <ClearIcon />
                    </IconButton>
                  </Tooltip>
                )}
              </Box>
            </InputAdornment>
          ),
        }}
        {...TextFieldProps}
      />

      {/* Voice search indicator */}
      {voiceState.isListening && (
        <Box
          sx={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            height: 3,
            bgcolor: 'error.main',
            animation: 'pulse 1.5s ease-in-out infinite',
            '@keyframes pulse': {
              '0%, 100%': {
                opacity: 1,
              },
              '50%': {
                opacity: 0.5,
              },
            },
          }}
        />
      )}
    </Paper>
  );
};

export default MobileSearchBar;
