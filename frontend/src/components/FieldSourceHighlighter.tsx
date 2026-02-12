import React from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Stack,
  Tooltip,
  IconButton,
  alpha,
  useTheme,
} from '@mui/material';
import {
  ContentCopy as CopyIcon,
  Visibility as ViewIcon,
  VisibilityOff as HideIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import type { SourceTextLocation } from '../types/parsingCorrection';

/**
 * Confidence level configuration
 */
type ConfidenceLevel = 'high' | 'medium' | 'low';

/**
 * Get confidence level from score
 */
const getConfidenceLevel = (confidence?: number): ConfidenceLevel => {
  if (confidence === undefined) return 'medium';
  if (confidence >= 0.8) return 'high';
  if (confidence >= 0.5) return 'medium';
  return 'low';
};

/**
 * Get confidence configuration for display
 */
const getConfidenceConfig = (level: ConfidenceLevel) => {
  switch (level) {
    case 'high':
      return {
        color: 'success' as const,
        icon: <CheckIcon fontSize="small" />,
        label: 'High Confidence',
      };
    case 'low':
      return {
        color: 'warning' as const,
        icon: <WarningIcon fontSize="small" />,
        label: 'Low Confidence',
      };
    case 'medium':
    default:
      return {
        color: 'info' as const,
        icon: <InfoIcon fontSize="small" />,
        label: 'Medium Confidence',
      };
  }
};

/**
 * FieldSourceHighlighter Component Props
 */
interface FieldSourceHighlighterProps {
  /** Name of the field being highlighted */
  fieldName: string;
  /** The extracted value for this field */
  extractedValue: string | Record<string, unknown>;
  /** Source text location information */
  sourceLocation?: SourceTextLocation | null;
  /** Full source text for context (if sourceLocation only has position) */
  fullSourceText?: string;
  /** Confidence score of extraction (0-1) */
  confidence?: number;
  /** Whether the field has been manually corrected */
  isCorrected?: boolean;
  /** Whether to show expanded view by default */
  defaultExpanded?: boolean;
  /** Maximum height for source text before scroll */
  maxHeight?: number;
  /** Click handler for selecting this field */
  onClick?: () => void;
  /** Whether this field is currently selected */
  isSelected?: boolean;
}

/**
 * Extract text snippet from full source using position
 */
const extractTextSnippet = (
  fullText: string | undefined,
  start: number | undefined,
  end: number | undefined,
  contextChars: number = 50
): { snippet: string; prefix: string; suffix: string; highlightStart: number; highlightEnd: number } => {
  if (!fullText || start === undefined || end === undefined) {
    return { snippet: '', prefix: '', suffix: '', highlightStart: 0, highlightEnd: 0 };
  }

  const prefix = fullText.slice(Math.max(0, start - contextChars), start);
  const suffix = fullText.slice(end, Math.min(fullText.length, end + contextChars));
  const highlightText = fullText.slice(start, end);

  return {
    snippet: highlightText,
    prefix: prefix.length < start ? '...' + prefix : prefix,
    suffix: suffix.length + end < fullText.length ? suffix + '...' : suffix,
    highlightStart: prefix.length < start ? 3 : 0,
    highlightEnd: (prefix.length < start ? 3 : 0) + highlightText.length,
  };
};

/**
 * FieldSourceHighlighter Component
 *
 * Displays the source text for a specific extracted field with:
 * - Visual highlighting of the relevant section
 * - Confidence indicator
 * - Copy to clipboard functionality
 * - Correction status badge
 * - Expandable/collapsible view
 *
 * @example
 * ```tsx
 * <FieldSourceHighlighter
 *   fieldName="position"
 *   extractedValue="Senior Software Engineer"
 *   sourceLocation={{ text: "Senior Software Engineer at Google", start: 0, end: 24 }}
 *   confidence={0.95}
 * />
 * ```
 */
const FieldSourceHighlighter: React.FC<FieldSourceHighlighterProps> = ({
  fieldName,
  extractedValue,
  sourceLocation,
  fullSourceText,
  confidence,
  isCorrected = false,
  defaultExpanded = true,
  maxHeight = 200,
  onClick,
  isSelected = false,
}) => {
  const { t } = useTranslation();
  const theme = useTheme();
  const [isExpanded, setIsExpanded] = React.useState(defaultExpanded);
  const [copied, setCopied] = React.useState(false);

  const confidenceLevel = getConfidenceLevel(confidence);
  const confidenceConfig = getConfidenceConfig(confidenceLevel);

  /**
   * Get display text - prefer direct text from location, otherwise extract from full text
   */
  const getDisplayText = (): {
    prefix: string;
    highlight: string;
    suffix: string;
  } => {
    if (sourceLocation?.text) {
      // Direct text available
      return {
        prefix: '',
        highlight: sourceLocation.text,
        suffix: '',
      };
    }

    if (fullSourceText && sourceLocation?.start !== undefined && sourceLocation?.end !== undefined) {
      // Extract from full text using positions
      const extracted = extractTextSnippet(
        fullSourceText,
        sourceLocation.start,
        sourceLocation.end
      );
      return {
        prefix: extracted.prefix,
        highlight: extracted.snippet,
        suffix: extracted.suffix,
      };
    }

    return { prefix: '', highlight: '', suffix: '' };
  };

  const displayText = getDisplayText();
  const hasSourceText = displayText.highlight.length > 0;

  /**
   * Format extracted value for display
   */
  const formatExtractedValue = (): string => {
    if (typeof extractedValue === 'string') {
      return extractedValue;
    }
    if (extractedValue && typeof extractedValue === 'object') {
      return JSON.stringify(extractedValue, null, 2);
    }
    return t('fieldSourceHighlighter.noValue', 'No value extracted');
  };

  /**
   * Copy source text to clipboard
   */
  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation();
    const textToCopy = displayText.prefix + displayText.highlight + displayText.suffix;
    try {
      await navigator.clipboard.writeText(textToCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard API not available
    }
  };

  /**
   * Toggle expanded state
   */
  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsExpanded(!isExpanded);
  };

  /**
   * Handle click on component
   */
  const handleClick = () => {
    onClick?.();
  };

  return (
    <Paper
      elevation={isSelected ? 3 : 1}
      onClick={handleClick}
      sx={{
        p: 2,
        cursor: onClick ? 'pointer' : 'default',
        border: 2,
        borderColor: isSelected
          ? 'primary.main'
          : isCorrected
          ? 'success.main'
          : 'divider',
        transition: 'all 0.2s ease-in-out',
        '&:hover': onClick
          ? {
              borderColor: 'primary.light',
              boxShadow: theme.shadows[2],
            }
          : {},
      }}
    >
      <Stack spacing={1.5}>
        {/* Header Row */}
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: 1,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="subtitle2" fontWeight={600} color="text.primary">
              {fieldName}
            </Typography>
            {isCorrected && (
              <Chip
                label={t('fieldSourceHighlighter.corrected', 'Corrected')}
                size="small"
                color="success"
                icon={<CheckIcon />}
              />
            )}
          </Box>
          <Stack direction="row" spacing={1} alignItems="center">
            {confidence !== undefined && (
              <Tooltip title={`${confidenceConfig.label}: ${Math.round(confidence * 100)}%`}>
                <Chip
                  icon={confidenceConfig.icon}
                  label={`${Math.round(confidence * 100)}%`}
                  size="small"
                  color={confidenceConfig.color}
                  variant="outlined"
                />
              </Tooltip>
            )}
            {hasSourceText && (
              <Tooltip title={isExpanded ? t('common.collapse') : t('common.expand')}>
                <IconButton size="small" onClick={handleToggle}>
                  {isExpanded ? <HideIcon fontSize="small" /> : <ViewIcon fontSize="small" />}
                </IconButton>
              </Tooltip>
            )}
          </Stack>
        </Box>

        {/* Extracted Value */}
        <Box>
          <Typography
            variant="caption"
            color="text.secondary"
            fontWeight={500}
            sx={{ display: 'block', mb: 0.5 }}
          >
            {t('fieldSourceHighlighter.extractedValue', 'Extracted Value')}:
          </Typography>
          <Box
            sx={{
              bgcolor: 'action.hover',
              borderRadius: 1,
              p: 1,
              border: 1,
              borderColor: 'divider',
            }}
          >
            <Typography
              variant="body2"
              sx={{
                fontFamily: typeof extractedValue === 'object' ? 'monospace' : 'inherit',
                whiteSpace: typeof extractedValue === 'object' ? 'pre-wrap' : 'normal',
                wordBreak: 'break-word',
              }}
            >
              {formatExtractedValue()}
            </Typography>
          </Box>
        </Box>

        {/* Source Text with Highlighting */}
        {hasSourceText && isExpanded && (
          <Box>
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                mb: 0.5,
              }}
            >
              <Typography
                variant="caption"
                color="text.secondary"
                fontWeight={500}
              >
                {t('fieldSourceHighlighter.sourceText', 'Source Text')}:
              </Typography>
              <Tooltip title={copied ? t('common.copied') : t('common.copy')}>
                <IconButton size="small" onClick={handleCopy}>
                  <CopyIcon fontSize="small" color={copied ? 'success' : 'action'} />
                </IconButton>
              </Tooltip>
            </Box>
            <Box
              sx={{
                bgcolor: alpha(theme.palette.primary.main, 0.05),
                borderRadius: 1,
                p: 1.5,
                border: 1,
                borderColor: 'divider',
                maxHeight,
                overflow: 'auto',
                position: 'relative',
              }}
            >
              <Typography
                variant="body2"
                sx={{
                  fontFamily: 'monospace',
                  fontSize: '0.8rem',
                  lineHeight: 1.6,
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}
              >
                {displayText.prefix && (
                  <Box component="span" sx={{ color: 'text.secondary' }}>
                    {displayText.prefix}
                  </Box>
                )}
                <Box
                  component="span"
                  sx={{
                    bgcolor: alpha(theme.palette.primary.main, 0.2),
                    color: 'primary.dark',
                    px: 0.5,
                    borderRadius: 0.5,
                    fontWeight: 500,
                  }}
                >
                  {displayText.highlight}
                </Box>
                {displayText.suffix && (
                  <Box component="span" sx={{ color: 'text.secondary' }}>
                    {displayText.suffix}
                  </Box>
                )}
              </Typography>
            </Box>

            {/* Location Info */}
            {(sourceLocation?.page || sourceLocation?.bbox) && (
              <Box sx={{ mt: 1 }}>
                <Stack direction="row" spacing={1}>
                  {sourceLocation.page && (
                    <Chip
                      label={t('fieldSourceHighlighter.page', 'Page {{page}}', {
                        page: sourceLocation.page,
                      })}
                      size="small"
                      variant="outlined"
                    />
                  )}
                </Stack>
              </Box>
            )}
          </Box>
        )}

        {/* No Source Text Available */}
        {!hasSourceText && (
          <Box>
            <Typography variant="caption" color="text.secondary" fontStyle="italic">
              {t('fieldSourceHighlighter.noSourceText', 'No source text location available')}
            </Typography>
          </Box>
        )}
      </Stack>
    </Paper>
  );
};

export default FieldSourceHighlighter;
export type { FieldSourceHighlighterProps, ConfidenceLevel };
