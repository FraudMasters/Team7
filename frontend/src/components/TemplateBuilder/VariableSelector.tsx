/**
 * Variable Selector Component
 *
 * Provides a UI for browsing and inserting dynamic variables into template content.
 * Variables are displayed with their descriptions and can be inserted with a single click.
 * Supports categorized variables for better organization.
 */

import { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Stack,
  Paper,
  TextField,
  Chip,
  IconButton,
  Tooltip,
  Popover,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  ListSubheader,
  Divider,
  InputAdornment,
} from '@mui/material';
import {
  Add as AddIcon,
  Search as SearchIcon,
  ContentCopy as CopyIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import type { TemplateVariable } from '../../types/templates';

interface VariableSelectorProps {
  /**
   * Callback when a variable is selected
   * Receives the variable name wrapped in {{}}
   */
  onVariableSelect: (variableTag: string) => void;

  /**
   * Optional custom list of variables
   * If not provided, uses default predefined variables
   */
  variables?: TemplateVariable[];

  /**
   * Optional anchor element for popover mode
   * If provided, displays as a popover; otherwise as inline component
   */
  anchorEl?: HTMLElement | null;

  /**
   * Callback when popover should close (popover mode only)
   */
  onClose?: () => void;

  /**
   * Whether to show the variable selector inline (default) or as a popover
   */
  variant?: 'inline' | 'popover';
}

/**
 * Default variable definitions organized by category
 */
const DEFAULT_VARIABLES: Record<string, TemplateVariable[]> = {
  'Candidate Information': [
    {
      name: 'candidate_name',
      label: 'Candidate Name',
      description: 'Full name of the candidate',
      type: 'string',
      example: 'John Doe',
    },
    {
      name: 'candidate_first_name',
      label: 'First Name',
      description: 'Candidate\'s first name',
      type: 'string',
      example: 'John',
    },
    {
      name: 'candidate_last_name',
      label: 'Last Name',
      description: 'Candidate\'s last name',
      type: 'string',
      example: 'Doe',
    },
    {
      name: 'candidate_email',
      label: 'Email Address',
      description: 'Candidate\'s email address',
      type: 'string',
      example: 'john.doe@example.com',
    },
    {
      name: 'candidate_phone',
      label: 'Phone Number',
      description: 'Candidate\'s phone number',
      type: 'string',
      example: '+1 (555) 123-4567',
    },
  ],
  'Job Information': [
    {
      name: 'job_title',
      label: 'Job Title',
      description: 'Title of the position',
      type: 'string',
      example: 'Senior Software Engineer',
    },
    {
      name: 'job_department',
      label: 'Department',
      description: 'Department hiring for the position',
      type: 'string',
      example: 'Engineering',
    },
    {
      name: 'job_location',
      label: 'Job Location',
      description: 'Location of the job',
      type: 'string',
      example: 'San Francisco, CA',
    },
    {
      name: 'job_type',
      label: 'Job Type',
      description: 'Employment type (Full-time, Part-time, etc.)',
      type: 'string',
      example: 'Full-time',
    },
  ],
  'Company Information': [
    {
      name: 'company_name',
      label: 'Company Name',
      description: 'Name of the company',
      type: 'string',
      example: 'Acme Corporation',
    },
    {
      name: 'company_website',
      label: 'Company Website',
      description: 'Company website URL',
      type: 'string',
      example: 'https://www.acme.com',
    },
    {
      name: 'recruiter_name',
      label: 'Recruiter Name',
      description: 'Name of the assigned recruiter',
      type: 'string',
      example: 'Jane Smith',
    },
    {
      name: 'recruiter_email',
      label: 'Recruiter Email',
      description: 'Email of the assigned recruiter',
      type: 'string',
      example: 'jane.smith@acme.com',
    },
  ],
  'Interview Information': [
    {
      name: 'interview_date',
      label: 'Interview Date',
      description: 'Date of the scheduled interview',
      type: 'date',
      example: 'March 25, 2026',
    },
    {
      name: 'interview_time',
      label: 'Interview Time',
      description: 'Time of the scheduled interview',
      type: 'string',
      example: '2:00 PM EST',
    },
    {
      name: 'interview_location',
      label: 'Interview Location',
      description: 'Location or meeting link for interview',
      type: 'string',
      example: 'https://meet.acme.com/interview-123',
    },
    {
      name: 'interview_duration',
      label: 'Interview Duration',
      description: 'Expected duration of the interview',
      type: 'string',
      example: '45 minutes',
    },
    {
      name: 'interviewer_name',
      label: 'Interviewer Name',
      description: 'Name of the interviewer',
      type: 'string',
      example: 'Sarah Johnson',
    },
  ],
  'Application Links': [
    {
      name: 'application_url',
      label: 'Application URL',
      description: 'Link to view the candidate\'s application',
      type: 'string',
      example: 'https://portal.acme.com/applications/123',
    },
    {
      name: 'portal_url',
      label: 'Candidate Portal',
      description: 'Link to the candidate portal',
      type: 'string',
      example: 'https://portal.acme.com',
    },
    {
      name: 'unsubscribe_url',
      label: 'Unsubscribe Link',
      description: 'Link for candidates to unsubscribe',
      type: 'string',
      example: 'https://portal.acme.com/unsubscribe',
    },
  ],
  'Pipeline Information': [
    {
      name: 'pipeline_stage',
      label: 'Pipeline Stage',
      description: 'Current stage in the hiring pipeline',
      type: 'string',
      example: 'interview_scheduled',
    },
    {
      name: 'application_date',
      label: 'Application Date',
      description: 'Date when candidate applied',
      type: 'date',
      example: 'March 15, 2026',
    },
  ],
};

export function VariableSelector({
  onVariableSelect,
  variables,
  anchorEl,
  onClose,
  variant = 'inline',
}: VariableSelectorProps) {
  const [searchQuery, setSearchQuery] = useState('');

  // Use provided variables or default ones
  const variablesByCategory = variables
    ? { 'Available Variables': variables }
    : DEFAULT_VARIABLES;

  // Filter variables based on search query
  const filteredVariables = Object.entries(variablesByCategory).reduce(
    (acc, [category, vars]) => {
      const filtered = vars.filter(
        (v) =>
          v.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          v.label?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          v.description?.toLowerCase().includes(searchQuery.toLowerCase())
      );
      if (filtered.length > 0) {
        acc[category] = filtered;
      }
      return acc;
    },
    {} as Record<string, TemplateVariable[]>
  );

  const handleVariableClick = (variableName: string) => {
    const variableTag = `{{${variableName}}}`;
    onVariableSelect(variableTag);

    // Close popover if in popover mode
    if (variant === 'popover' && onClose) {
      onClose();
    }
  };

  const handleCopyVariable = (variableName: string, event: React.MouseEvent) => {
    event.stopPropagation();
    const variableTag = `{{${variableName}}}`;
    navigator.clipboard.writeText(variableTag);
  };

  const renderContent = () => (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="h6" component="h3">
            Insert Variable
          </Typography>
          {variant === 'popover' && onClose && (
            <IconButton size="small" onClick={onClose}>
              <CloseIcon fontSize="small" />
            </IconButton>
          )}
        </Box>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Click on a variable to insert it into your template
        </Typography>

        {/* Search */}
        <TextField
          fullWidth
          size="small"
          placeholder="Search variables..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" />
              </InputAdornment>
            ),
          }}
          sx={{ mt: 1 }}
        />
      </Box>

      {/* Variable List */}
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        {Object.keys(filteredVariables).length === 0 ? (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              No variables found matching "{searchQuery}"
            </Typography>
          </Box>
        ) : (
          <List sx={{ py: 0 }}>
            {Object.entries(filteredVariables).map(([category, vars], categoryIndex) => (
              <Box key={category}>
                <ListSubheader
                  sx={{
                    bgcolor: 'background.paper',
                    borderBottom: 1,
                    borderColor: 'divider',
                    py: 1,
                  }}
                >
                  <Typography variant="caption" fontWeight="bold" color="primary">
                    {category}
                  </Typography>
                </ListSubheader>
                {vars.map((variable, index) => (
                  <ListItem
                    key={variable.name}
                    disablePadding
                    divider={index < vars.length - 1}
                    secondaryAction={
                      <Tooltip title="Copy to clipboard">
                        <IconButton
                          edge="end"
                          size="small"
                          onClick={(e) => handleCopyVariable(variable.name, e)}
                        >
                          <CopyIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    }
                  >
                    <ListItemButton onClick={() => handleVariableClick(variable.name)}>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Chip
                              label={`{{${variable.name}}}`}
                              size="small"
                              variant="outlined"
                              sx={{
                                fontFamily: 'monospace',
                                fontSize: '0.75rem',
                                height: 24,
                              }}
                            />
                            {variable.label && (
                              <Typography variant="body2" fontWeight="medium">
                                {variable.label}
                              </Typography>
                            )}
                          </Box>
                        }
                        secondary={
                          <Stack spacing={0.5} sx={{ mt: 0.5 }}>
                            {variable.description && (
                              <Typography variant="caption" color="text.secondary">
                                {variable.description}
                              </Typography>
                            )}
                            {variable.example && (
                              <Typography
                                variant="caption"
                                sx={{
                                  color: 'success.main',
                                  fontStyle: 'italic',
                                }}
                              >
                                Example: {String(variable.example)}
                              </Typography>
                            )}
                          </Stack>
                        }
                      />
                    </ListItemButton>
                  </ListItem>
                ))}
                {categoryIndex < Object.keys(filteredVariables).length - 1 && (
                  <Divider sx={{ my: 1 }} />
                )}
              </Box>
            ))}
          </List>
        )}
      </Box>

      {/* Footer */}
      <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider', bgcolor: 'background.default' }}>
        <Typography variant="caption" color="text.secondary">
          <strong>Tip:</strong> Variables use the syntax{' '}
          <code style={{ background: '#f5f5f5', padding: '2px 4px', borderRadius: 2 }}>
            {`{{variable_name}}`}
          </code>
        </Typography>
      </Box>
    </Box>
  );

  // Render as popover if anchorEl is provided
  if (variant === 'popover') {
    return (
      <Popover
        open={Boolean(anchorEl)}
        anchorEl={anchorEl}
        onClose={onClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'left',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'left',
        }}
        PaperProps={{
          sx: {
            width: 500,
            maxHeight: 600,
            display: 'flex',
            flexDirection: 'column',
          },
        }}
      >
        {renderContent()}
      </Popover>
    );
  }

  // Render as inline Paper component
  return (
    <Paper
      elevation={2}
      sx={{
        width: '100%',
        maxWidth: 500,
        height: 600,
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {renderContent()}
    </Paper>
  );
}

/**
 * Variable Selector Button
 *
 * A button that opens the variable selector in popover mode
 * and inserts the selected variable at the cursor position in a text field.
 */
interface VariableSelectorButtonProps {
  /**
   * Callback when a variable is selected
   * Receives the variable name wrapped in {{}}
   */
  onVariableSelect: (variableTag: string) => void;

  /**
   * Optional custom list of variables
   */
  variables?: TemplateVariable[];

  /**
   * Button variant
   */
  variant?: 'text' | 'outlined' | 'contained';

  /**
   * Button size
   */
  size?: 'small' | 'medium' | 'large';

  /**
   * Whether the button is disabled
   */
  disabled?: boolean;
}

export function VariableSelectorButton({
  onVariableSelect,
  variables,
  variant = 'outlined',
  size = 'small',
  disabled = false,
}: VariableSelectorButtonProps) {
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleVariableSelect = (variableTag: string) => {
    onVariableSelect(variableTag);
    handleClose();
  };

  return (
    <>
      <Button
        variant={variant}
        size={size}
        startIcon={<AddIcon />}
        onClick={handleClick}
        disabled={disabled}
      >
        Insert Variable
      </Button>
      <VariableSelector
        variant="popover"
        anchorEl={anchorEl}
        onClose={handleClose}
        onVariableSelect={handleVariableSelect}
        variables={variables}
      />
    </>
  );
}

export default VariableSelector;
