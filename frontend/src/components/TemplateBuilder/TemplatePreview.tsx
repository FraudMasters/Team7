/**
 * Template Preview Component
 *
 * Real-time preview of notification templates with sample data substitution.
 * Displays email and SMS templates with proper formatting and variable replacement.
 */

import { useMemo } from 'react';
import {
  Box,
  Typography,
  Paper,
  Stack,
  Divider,
  Button,
  Chip,
  Alert,
} from '@mui/material';
import {
  Email as EmailIcon,
  Sms as SmsIcon,
  Person as PersonIcon,
  Business as CompanyIcon,
  CalendarToday as CalendarIcon,
} from '@mui/icons-material';
import type {
  TemplateBlock,
  TextBlock,
  HeadingBlock,
  ButtonBlock,
  ConditionalBlock,
  NotificationTemplateType,
  TemplateVariableContext,
  TemplateCondition,
  TemplateVariableValue,
} from '../../types/templates';

interface TemplatePreviewProps {
  /**
   * Template type (email or SMS)
   */
  type: NotificationTemplateType;

  /**
   * Email subject (only for email templates)
   */
  subject?: string;

  /**
   * Template blocks to render
   */
  blocks: TemplateBlock[];

  /**
   * Optional custom variable values for preview
   * If not provided, uses default sample data
   */
  variables?: TemplateVariableContext;

  /**
   * Whether to show variable tags
   */
  showVariableTags?: boolean;
}

/**
 * Default sample data for template preview
 */
const DEFAULT_SAMPLE_DATA: TemplateVariableContext = {
  // Candidate Information
  candidate_name: 'Jane Smith',
  candidate_first_name: 'Jane',
  candidate_last_name: 'Smith',
  candidate_email: 'jane.smith@example.com',
  candidate_phone: '+1 (555) 123-4567',

  // Job Information
  job_title: 'Senior Software Engineer',
  job_department: 'Engineering',
  job_location: 'San Francisco, CA',
  job_type: 'Full-time',

  // Company Information
  company_name: 'Acme Corporation',
  company_website: 'https://www.acme.com',
  recruiter_name: 'John Davis',
  recruiter_email: 'john.davis@acme.com',

  // Interview Information
  interview_date: 'March 28, 2026',
  interview_time: '2:00 PM PST',
  interview_location: 'https://meet.acme.com/interview-abc123',
  interview_duration: '45 minutes',
  interviewer_name: 'Sarah Johnson',

  // Application Links
  application_url: 'https://portal.acme.com/applications/12345',
  portal_url: 'https://portal.acme.com',
  unsubscribe_url: 'https://portal.acme.com/unsubscribe',

  // Pipeline Information
  pipeline_stage: 'interview_scheduled',
  application_date: 'March 15, 2026',
};

/**
 * Substitute variables in a string with sample data
 */
function substituteVariables(
  text: string,
  variables: TemplateVariableContext,
  showTags: boolean = false
): string {
  if (!text) return '';

  return text.replace(/\{\{([^}]+)\}\}/g, (match, varName) => {
    const trimmedVarName = varName.trim();
    const value = variables[trimmedVarName];

    if (value === undefined || value === null) {
      // Show placeholder if variable not found
      return showTags ? match : `[${trimmedVarName}]`;
    }

    // Convert value to string
    if (Array.isArray(value)) {
      return value.join(', ');
    }

    return String(value);
  });
}

/**
 * Evaluate a conditional expression
 */
function evaluateCondition(
  condition: TemplateCondition,
  variables: TemplateVariableContext
): boolean {
  const fieldValue = variables[condition.field];
  const compareValue = condition.value;

  switch (condition.operator) {
    case 'eq':
      return fieldValue === compareValue;

    case 'ne':
      return fieldValue !== compareValue;

    case 'gt':
      return Number(fieldValue) > Number(compareValue);

    case 'lt':
      return Number(fieldValue) < Number(compareValue);

    case 'gte':
      return Number(fieldValue) >= Number(compareValue);

    case 'lte':
      return Number(fieldValue) <= Number(compareValue);

    case 'in':
      if (Array.isArray(compareValue)) {
        return compareValue.includes(fieldValue as string);
      }
      return false;

    case 'not_in':
      if (Array.isArray(compareValue)) {
        return !compareValue.includes(fieldValue as string);
      }
      return false;

    case 'contains':
      return String(fieldValue).includes(String(compareValue));

    default:
      return false;
  }
}

/**
 * Render a single template block with sample data
 */
function renderBlock(
  block: TemplateBlock,
  variables: TemplateVariableContext,
  showTags: boolean
): React.ReactNode {
  switch (block.type) {
    case 'text': {
      const textBlock = block as TextBlock;
      const content = substituteVariables(textBlock.content || '', variables, showTags);
      return (
        <Typography
          key={block.id}
          variant="body1"
          sx={{
            whiteSpace: 'pre-wrap',
            lineHeight: 1.7,
            color: 'text.primary',
          }}
        >
          {content}
        </Typography>
      );
    }

    case 'heading': {
      const headingBlock = block as HeadingBlock;
      const content = substituteVariables(headingBlock.content || '', variables, showTags);
      const level = headingBlock.level || 2;
      const variant = `h${level}` as 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6';

      return (
        <Typography
          key={block.id}
          variant={variant}
          sx={{
            fontWeight: 600,
            color: 'text.primary',
            mt: level <= 2 ? 2 : 1.5,
            mb: 1,
          }}
        >
          {content}
        </Typography>
      );
    }

    case 'button': {
      const buttonBlock = block as ButtonBlock;
      const content = substituteVariables(buttonBlock.content || '', variables, showTags);
      const href = substituteVariables(buttonBlock.href || '#', variables, showTags);
      const style = buttonBlock.style || 'primary';

      const buttonStyles = {
        primary: {
          bgcolor: 'primary.main',
          color: 'white',
          '&:hover': { bgcolor: 'primary.dark' },
        },
        secondary: {
          bgcolor: 'grey.300',
          color: 'text.primary',
          '&:hover': { bgcolor: 'grey.400' },
        },
        outline: {
          bgcolor: 'transparent',
          color: 'primary.main',
          border: 2,
          borderColor: 'primary.main',
          '&:hover': { bgcolor: 'primary.50' },
        },
      };

      return (
        <Box key={block.id} sx={{ my: 2 }}>
          <Button
            variant="contained"
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            sx={{
              ...buttonStyles[style],
              px: 3,
              py: 1.5,
              borderRadius: 1,
              textTransform: 'none',
              fontSize: '1rem',
              fontWeight: 600,
            }}
          >
            {content}
          </Button>
        </Box>
      );
    }

    case 'conditional': {
      const conditionalBlock = block as ConditionalBlock;
      const conditionMet = evaluateCondition(conditionalBlock.condition, variables);
      const blocksToRender = conditionMet
        ? conditionalBlock.true_blocks || []
        : conditionalBlock.false_blocks || [];

      return (
        <Box key={block.id} sx={{ my: 1 }}>
          {blocksToRender.map((nestedBlock) =>
            renderBlock(nestedBlock, variables, showTags)
          )}
        </Box>
      );
    }

    default:
      return null;
  }
}

export function TemplatePreview({
  type,
  subject = '',
  blocks,
  variables,
  showVariableTags = false,
}: TemplatePreviewProps) {
  // Merge custom variables with defaults
  const sampleData = useMemo(() => {
    return { ...DEFAULT_SAMPLE_DATA, ...variables };
  }, [variables]);

  // Substitute variables in subject
  const renderedSubject = useMemo(() => {
    return substituteVariables(subject, sampleData, showVariableTags);
  }, [subject, sampleData, showVariableTags]);

  // Check if template has content
  const hasContent = blocks.length > 0 || (type === 'email' && subject.trim());

  // Calculate character count for SMS
  const smsCharCount = useMemo(() => {
    if (type !== 'sms') return 0;

    const bodyText = blocks
      .map((block) => {
        if (block.type === 'text') {
          return substituteVariables((block as TextBlock).content || '', sampleData, showVariableTags);
        }
        return '';
      })
      .join('\n\n');

    return bodyText.length;
  }, [type, blocks, sampleData, showVariableTags]);

  // Calculate SMS segments (160 chars per segment)
  const smsSegments = Math.ceil(smsCharCount / 160) || 1;

  return (
    <Paper
      elevation={2}
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      {/* Preview Header */}
      <Box
        sx={{
          p: 2,
          bgcolor: type === 'email' ? 'primary.50' : 'secondary.50',
          borderBottom: 1,
          borderColor: 'divider',
        }}
      >
        <Stack direction="row" alignItems="center" spacing={1}>
          {type === 'email' ? (
            <EmailIcon color="primary" />
          ) : (
            <SmsIcon color="secondary" />
          )}
          <Typography variant="h6" fontWeight="medium">
            {type === 'email' ? 'Email Preview' : 'SMS Preview'}
          </Typography>
          {type === 'sms' && (
            <Chip
              label={`${smsCharCount} chars • ${smsSegments} segment${smsSegments !== 1 ? 's' : ''}`}
              size="small"
              color={smsCharCount > 160 ? 'warning' : 'default'}
            />
          )}
        </Stack>
      </Box>

      {/* Preview Content */}
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        {!hasContent ? (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              p: 4,
            }}
          >
            <Stack alignItems="center" spacing={2}>
              <Box
                sx={{
                  width: 80,
                  height: 80,
                  borderRadius: '50%',
                  bgcolor: 'action.hover',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                {type === 'email' ? (
                  <EmailIcon sx={{ fontSize: 40, color: 'text.secondary' }} />
                ) : (
                  <SmsIcon sx={{ fontSize: 40, color: 'text.secondary' }} />
                )}
              </Box>
              <Typography variant="body1" color="text.secondary" textAlign="center">
                Start building your template to see a preview
              </Typography>
              <Typography variant="caption" color="text.secondary" textAlign="center">
                The preview will update in real-time as you add content
              </Typography>
            </Stack>
          </Box>
        ) : type === 'email' ? (
          // Email Preview
          <Box sx={{ p: 3 }}>
            <Paper
              variant="outlined"
              sx={{
                maxWidth: 600,
                mx: 'auto',
                bgcolor: 'background.paper',
                boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
              }}
            >
              {/* Email Header */}
              <Box sx={{ p: 2, bgcolor: 'grey.100', borderBottom: 1, borderColor: 'divider' }}>
                <Stack spacing={1}>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <Typography variant="caption" color="text.secondary" sx={{ minWidth: 60 }}>
                      From:
                    </Typography>
                    <Stack direction="row" spacing={0.5} alignItems="center">
                      <CompanyIcon fontSize="small" color="action" />
                      <Typography variant="body2">
                        {sampleData.recruiter_name} ({sampleData.recruiter_email})
                      </Typography>
                    </Stack>
                  </Stack>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <Typography variant="caption" color="text.secondary" sx={{ minWidth: 60 }}>
                      To:
                    </Typography>
                    <Stack direction="row" spacing={0.5} alignItems="center">
                      <PersonIcon fontSize="small" color="action" />
                      <Typography variant="body2">
                        {sampleData.candidate_name} ({sampleData.candidate_email})
                      </Typography>
                    </Stack>
                  </Stack>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <Typography variant="caption" color="text.secondary" sx={{ minWidth: 60 }}>
                      Date:
                    </Typography>
                    <Stack direction="row" spacing={0.5} alignItems="center">
                      <CalendarIcon fontSize="small" color="action" />
                      <Typography variant="body2">
                        {new Date().toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </Typography>
                    </Stack>
                  </Stack>
                  <Divider sx={{ my: 1 }} />
                  <Typography variant="body1" fontWeight="bold">
                    Subject: {renderedSubject || '(No subject)'}
                  </Typography>
                </Stack>
              </Box>

              {/* Email Body */}
              <Box sx={{ p: 3 }}>
                <Stack spacing={2}>
                  {blocks.map((block) => renderBlock(block, sampleData, showVariableTags))}
                </Stack>
              </Box>

              {/* Email Footer */}
              <Box
                sx={{
                  p: 2,
                  mt: 3,
                  bgcolor: 'grey.50',
                  borderTop: 1,
                  borderColor: 'divider',
                }}
              >
                <Typography variant="caption" color="text.secondary" align="center" display="block">
                  {sampleData.company_name} • {sampleData.company_website}
                </Typography>
                <Typography variant="caption" color="text.secondary" align="center" display="block">
                  <a
                    href={String(sampleData.unsubscribe_url)}
                    style={{ color: 'inherit', textDecoration: 'underline' }}
                  >
                    Unsubscribe from these emails
                  </a>
                </Typography>
              </Box>
            </Paper>
          </Box>
        ) : (
          // SMS Preview
          <Box sx={{ p: 3 }}>
            <Stack spacing={2} alignItems="center">
              <Alert severity="info" sx={{ maxWidth: 400 }}>
                SMS messages are limited to 160 characters per segment. Longer messages will be split
                into multiple segments.
              </Alert>

              <Paper
                variant="outlined"
                sx={{
                  maxWidth: 360,
                  p: 2,
                  bgcolor: 'grey.100',
                  borderRadius: 3,
                  position: 'relative',
                }}
              >
                <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                  From: {sampleData.company_name}
                </Typography>
                <Divider sx={{ mb: 2 }} />

                <Box
                  sx={{
                    bgcolor: 'primary.main',
                    color: 'white',
                    p: 2,
                    borderRadius: 2,
                    borderBottomRightRadius: 0.5,
                    maxWidth: '85%',
                    ml: 'auto',
                  }}
                >
                  <Stack spacing={1.5}>
                    {blocks.map((block) => renderBlock(block, sampleData, showVariableTags))}
                  </Stack>
                </Box>

                <Typography
                  variant="caption"
                  color="text.secondary"
                  sx={{ mt: 1, display: 'block', textAlign: 'right' }}
                >
                  {new Date().toLocaleTimeString('en-US', {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </Typography>
              </Paper>

              {smsCharCount > 160 && (
                <Alert severity="warning" sx={{ maxWidth: 400 }}>
                  This message will be sent as {smsSegments} segments. Consider shortening the
                  message to reduce cost.
                </Alert>
              )}
            </Stack>
          </Box>
        )}
      </Box>

      {/* Sample Data Info */}
      <Box
        sx={{
          p: 2,
          bgcolor: 'background.default',
          borderTop: 1,
          borderColor: 'divider',
        }}
      >
        <Typography variant="caption" color="text.secondary">
          <strong>Preview Note:</strong> This preview uses sample data for variables. Actual values
          will be substituted when the template is sent to candidates.
        </Typography>
      </Box>
    </Paper>
  );
}

export default TemplatePreview;
