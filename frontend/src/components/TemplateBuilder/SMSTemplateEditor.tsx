/**
 * SMS Template Editor Component
 *
 * Specialized editor for SMS templates with character count and segment calculation.
 * Displays real-time character count and SMS segment information based on GSM-7 encoding.
 */

import { useState, useCallback, useMemo, useRef } from 'react';
import {
  Box,
  Typography,
  Paper,
  Stack,
  TextField,
  Alert,
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  Message as MessageIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { VariableSelectorButton } from './VariableSelector';

interface SMSTemplateEditorProps {
  /**
   * The SMS content
   */
  content: string;

  /**
   * Callback when content changes
   */
  onChange: (content: string) => void;

  /**
   * Optional placeholder text
   */
  placeholder?: string;

  /**
   * Whether the field is disabled
   */
  disabled?: boolean;

  /**
   * Whether the field is required
   */
  required?: boolean;
}

/**
 * Calculate SMS segment information
 *
 * SMS messages use GSM-7 encoding by default:
 * - Single segment: 160 characters
 * - Multi-segment: 153 characters per segment (7 chars used for concatenation header)
 *
 * If the message contains non-GSM-7 characters (emojis, special Unicode),
 * it falls back to UCS-2 encoding:
 * - Single segment: 70 characters
 * - Multi-segment: 67 characters per segment
 */
function calculateSMSSegments(text: string): {
  charCount: number;
  segmentCount: number;
  charsPerSegment: number;
  charsRemaining: number;
  encoding: 'GSM-7' | 'UCS-2';
} {
  const charCount = text.length;

  // GSM-7 basic character set
  const gsmCharacters = /^[@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞÆæßÉ !"#¤%&'()*+,\-./0-9:;<=>?¡A-ZÄÖÑÜ§¿a-zäöñüà\[\\\]\^\{\|\}~\€]*$/;

  // Detect encoding
  const isGSM7 = gsmCharacters.test(text);
  const encoding = isGSM7 ? 'GSM-7' : 'UCS-2';

  // Calculate segments based on encoding
  let segmentCount: number;
  let charsPerSegment: number;
  let maxChars: number;

  if (isGSM7) {
    // GSM-7 encoding
    if (charCount === 0) {
      segmentCount = 0;
      charsPerSegment = 160;
      maxChars = 160;
    } else if (charCount <= 160) {
      segmentCount = 1;
      charsPerSegment = 160;
      maxChars = 160;
    } else {
      segmentCount = Math.ceil(charCount / 153);
      charsPerSegment = 153;
      maxChars = segmentCount * 153;
    }
  } else {
    // UCS-2 encoding (Unicode)
    if (charCount === 0) {
      segmentCount = 0;
      charsPerSegment = 70;
      maxChars = 70;
    } else if (charCount <= 70) {
      segmentCount = 1;
      charsPerSegment = 70;
      maxChars = 70;
    } else {
      segmentCount = Math.ceil(charCount / 67);
      charsPerSegment = 67;
      maxChars = segmentCount * 67;
    }
  }

  const charsRemaining = maxChars - charCount;

  return {
    charCount,
    segmentCount,
    charsPerSegment,
    charsRemaining,
    encoding,
  };
}

export function SMSTemplateEditor({
  content,
  onChange,
  placeholder = 'Enter SMS content. Use {{variable_name}} for dynamic content.',
  disabled = false,
  required = false,
}: SMSTemplateEditorProps) {
  const textFieldRef = useRef<HTMLInputElement>(null);

  // Calculate SMS statistics
  const smsStats = useMemo(() => calculateSMSSegments(content), [content]);

  // Determine status based on character count
  const status = useMemo(() => {
    if (smsStats.charCount === 0) {
      return { severity: 'info' as const, message: 'Start typing your SMS message' };
    }

    if (smsStats.encoding === 'UCS-2') {
      return {
        severity: 'warning' as const,
        message: 'Message contains special characters (emoji, Unicode). Using UCS-2 encoding with reduced character limit.',
      };
    }

    if (smsStats.segmentCount > 3) {
      return {
        severity: 'warning' as const,
        message: `Message will be sent as ${smsStats.segmentCount} SMS segments. Consider shortening for better deliverability.`,
      };
    }

    if (smsStats.segmentCount > 1) {
      return {
        severity: 'info' as const,
        message: `Message will be sent as ${smsStats.segmentCount} SMS segments.`,
      };
    }

    return null;
  }, [smsStats]);

  // Calculate progress percentage for visual indicator
  const progressPercentage = useMemo(() => {
    const limit = smsStats.segmentCount <= 1 ? (smsStats.encoding === 'GSM-7' ? 160 : 70) : smsStats.charsPerSegment;
    const currentInSegment = smsStats.charCount % smsStats.charsPerSegment || smsStats.charCount;
    return Math.min((currentInSegment / limit) * 100, 100);
  }, [smsStats]);

  // Get color based on character count
  const progressColor = useMemo(() => {
    if (smsStats.segmentCount > 3) return 'warning';
    if (smsStats.segmentCount > 1) return 'info';
    if (progressPercentage > 90) return 'warning';
    return 'primary';
  }, [smsStats.segmentCount, progressPercentage]);

  // Handle variable insertion
  const handleVariableSelect = useCallback((variableTag: string) => {
    const input = textFieldRef.current;
    if (!input) {
      onChange(content + variableTag);
      return;
    }

    const start = input.selectionStart || 0;
    const end = input.selectionEnd || 0;
    const newContent =
      content.substring(0, start) +
      variableTag +
      content.substring(end);

    onChange(newContent);

    // Restore cursor position after the inserted variable
    setTimeout(() => {
      const newCursorPos = start + variableTag.length;
      input.setSelectionRange(newCursorPos, newCursorPos);
      input.focus();
    }, 0);
  }, [content, onChange]);

  return (
    <Paper sx={{ p: 3 }}>
      <Stack spacing={2}>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <MessageIcon color="primary" />
          <Typography variant="h6">SMS Content</Typography>
        </Box>

        {/* Text Editor */}
        <TextField
          inputRef={textFieldRef}
          multiline
          rows={6}
          fullWidth
          value={content}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          required={required}
          helperText="Use {{variable_name}} syntax for dynamic content"
        />

        {/* Variable Selector */}
        <Box>
          <VariableSelectorButton onVariableSelect={handleVariableSelect} />
        </Box>

        {/* Statistics Bar */}
        <Paper variant="outlined" sx={{ p: 2, bgcolor: 'background.default' }}>
          <Stack spacing={2}>
            {/* Character Count and Segments */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Stack direction="row" spacing={1} alignItems="center">
                <Typography variant="body2" fontWeight="medium">
                  Characters:
                </Typography>
                <Chip
                  label={`${smsStats.charCount} / ${smsStats.charsPerSegment}${smsStats.segmentCount > 1 ? ' per segment' : ''}`}
                  size="small"
                  color={smsStats.charsRemaining < 10 && smsStats.charCount > 0 ? 'warning' : 'default'}
                />
              </Stack>

              <Stack direction="row" spacing={1} alignItems="center">
                <Typography variant="body2" fontWeight="medium">
                  Segments:
                </Typography>
                <Chip
                  label={smsStats.segmentCount}
                  size="small"
                  color={smsStats.segmentCount > 3 ? 'warning' : smsStats.segmentCount > 1 ? 'info' : 'success'}
                  icon={smsStats.segmentCount > 3 ? <WarningIcon /> : undefined}
                />
              </Stack>

              <Stack direction="row" spacing={1} alignItems="center">
                <Typography variant="body2" fontWeight="medium">
                  Encoding:
                </Typography>
                <Chip
                  label={smsStats.encoding}
                  size="small"
                  color={smsStats.encoding === 'UCS-2' ? 'warning' : 'default'}
                />
              </Stack>
            </Box>

            {/* Progress Bar */}
            <Box>
              <LinearProgress
                variant="determinate"
                value={progressPercentage}
                color={progressColor}
                sx={{ height: 8, borderRadius: 1 }}
              />
              <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                {smsStats.charsRemaining > 0
                  ? `${smsStats.charsRemaining} character${smsStats.charsRemaining !== 1 ? 's' : ''} remaining in current segment`
                  : 'Segment limit reached'}
              </Typography>
            </Box>
          </Stack>
        </Paper>

        {/* Status Alert */}
        {status && (
          <Alert severity={status.severity} icon={status.severity === 'warning' ? <WarningIcon /> : undefined}>
            {status.message}
          </Alert>
        )}

        {/* SMS Encoding Info */}
        <Alert severity="info" sx={{ fontSize: '0.875rem' }}>
          <Typography variant="body2" fontWeight="medium" gutterBottom>
            SMS Encoding Information:
          </Typography>
          <Typography variant="caption" component="div">
            • <strong>GSM-7:</strong> Standard SMS (160 chars single, 153 chars per multi-segment)
          </Typography>
          <Typography variant="caption" component="div">
            • <strong>UCS-2:</strong> Unicode/Emoji (70 chars single, 67 chars per multi-segment)
          </Typography>
          <Typography variant="caption" component="div" sx={{ mt: 0.5 }}>
            Carrier charges may apply per segment. Keep messages concise for best results.
          </Typography>
        </Alert>
      </Stack>
    </Paper>
  );
}
