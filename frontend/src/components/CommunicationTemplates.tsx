/**
 * Communication Templates Component
 *
 * Manage communication templates with variable substitution support.
 */

import { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Stack,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  IconButton,
  Grid2,
  Paper,
  Alert,
  CircularProgress,
  Menu,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Chip,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Description as DescriptionIcon,
  Close as CloseIcon,
  MoreVert as MoreVertIcon,
  Preview as PreviewIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { communicationTemplatesClient } from '../api/communicationTemplates';
import type {
  CommunicationTemplateResponse,
  TemplateType,
  TemplateCategory,
} from '../api/communicationTemplates';

interface CommunicationTemplatesProps {
  type?: TemplateType;
  candidateId?: string;
  readOnly?: boolean;
  onTemplateSelect?: (template: CommunicationTemplateResponse) => void;
}

const TEMPLATE_TYPE_LABELS: Record<TemplateType, string> = {
  email: 'Email',
  sms: 'SMS',
  in_system: 'In-System',
};

const TEMPLATE_TYPE_COLORS: Record<TemplateType, string> = {
  email: '#1976D2',
  sms: '#7B1FA2',
  in_system: '#388E3C',
};

const TEMPLATE_CATEGORY_LABELS: Record<TemplateCategory, string> = {
  outreach: 'Outreach',
  interview: 'Interview',
  rejection: 'Rejection',
  offer: 'Offer',
  follow_up: 'Follow Up',
  other: 'Other',
};

export function CommunicationTemplates({
  type,
  candidateId,
  readOnly = false,
  onTemplateSelect,
}: CommunicationTemplatesProps) {
  const queryClient = useQueryClient();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<CommunicationTemplateResponse | null>(null);
  const [templateName, setTemplateName] = useState('');
  const [templateType, setTemplateType] = useState<TemplateType>('email');
  const [templateCategory, setTemplateCategory] = useState<TemplateCategory>('other');
  const [templateSubject, setTemplateSubject] = useState('');
  const [templateBody, setTemplateBody] = useState('');
  const [templateVariables, setTemplateVariables] = useState<string[]>([]);
  const [templateDescription, setTemplateDescription] = useState('');
  const [isActive, setIsActive] = useState(true);
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const [previewData, setPreviewData] = useState<{ subject?: string; body: string } | null>(null);

  // Fetch templates
  const { data: templatesData, isLoading: templatesLoading } = useQuery({
    queryKey: ['communication-templates', type],
    queryFn: async () => {
      return await communicationTemplatesClient.listTemplates(
        0,
        100,
        type,
        undefined,
        undefined,
        undefined
      );
    },
  });

  const templates = templatesData?.templates || [];

  // Create template mutation
  const createMutation = useMutation({
    mutationFn: async (data: {
      name: string;
      type: TemplateType;
      category: TemplateCategory;
      subject?: string;
      body: string;
      variables: string[];
      description?: string;
      is_active: boolean;
    }) => {
      return await communicationTemplatesClient.createTemplate(data);
    },
    onSuccess: () => {
      setDialogOpen(false);
      resetForm();
      queryClient.invalidateQueries({ queryKey: ['communication-templates'] });
    },
  });

  // Update template mutation
  const updateMutation = useMutation({
    mutationFn: async ({
      id,
      data,
    }: {
      id: string;
      data: {
        name?: string;
        type?: TemplateType;
        category?: TemplateCategory;
        subject?: string;
        body?: string;
        variables?: string[];
        description?: string;
        is_active?: boolean;
      };
    }) => {
      return await communicationTemplatesClient.updateTemplate(id, data);
    },
    onSuccess: () => {
      setDialogOpen(false);
      setSelectedTemplate(null);
      queryClient.invalidateQueries({ queryKey: ['communication-templates'] });
    },
  });

  // Delete template mutation
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await communicationTemplatesClient.deleteTemplate(id);
    },
    onSuccess: () => {
      setDeleteDialogOpen(false);
      setSelectedTemplate(null);
      queryClient.invalidateQueries({ queryKey: ['communication-templates'] });
    },
  });

  // Preview template mutation
  const previewMutation = useMutation({
    mutationFn: async ({ templateId, variables }: { templateId: string; variables: Record<string, string> }) => {
      return await communicationTemplatesClient.previewTemplate(templateId, { variables });
    },
    onSuccess: (data) => {
      setPreviewData({ subject: data.subject, body: data.body });
      setPreviewDialogOpen(true);
    },
  });

  const resetForm = () => {
    setTemplateName('');
    setTemplateType('email');
    setTemplateCategory('other');
    setTemplateSubject('');
    setTemplateBody('');
    setTemplateVariables([]);
    setTemplateDescription('');
    setIsActive(true);
    setSelectedTemplate(null);
    setEditMode(false);
  };

  const handleOpenCreateDialog = () => {
    resetForm();
    if (type) {
      setTemplateType(type);
    }
    setDialogOpen(true);
  };

  const handleOpenEditDialog = (template: CommunicationTemplateResponse) => {
    setEditMode(true);
    setSelectedTemplate(template);
    setTemplateName(template.name);
    setTemplateType(template.type);
    setTemplateCategory(template.category || 'other');
    setTemplateSubject(template.subject || '');
    setTemplateBody(template.body);
    setTemplateVariables(template.variables || []);
    setTemplateDescription(template.description || '');
    setIsActive(template.is_active);
    setDialogOpen(true);
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, template: CommunicationTemplateResponse) => {
    setMenuAnchor(event.currentTarget);
    setSelectedTemplate(template);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
    setSelectedTemplate(null);
  };

  const handleSaveTemplate = () => {
    if (!templateName.trim() || !templateBody.trim()) return;

    const data = {
      name: templateName.trim(),
      type: templateType,
      category: templateCategory,
      subject: templateType === 'email' ? templateSubject : undefined,
      body: templateBody,
      variables: templateVariables,
      description: templateDescription,
      is_active: isActive,
    };

    if (editMode && selectedTemplate) {
      updateMutation.mutate({ id: selectedTemplate.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  const handleDeleteClick = () => {
    setDeleteDialogOpen(true);
    handleMenuClose();
  };

  const handleDeleteConfirm = () => {
    if (selectedTemplate) {
      deleteMutation.mutate(selectedTemplate.id);
    }
  };

  const handlePreviewClick = (template: CommunicationTemplateResponse) => {
    // Extract variables from template
    const variableRegex = /\{\{(\w+)\}\}/g;
    const variables = new Set<string>();

    if (template.subject) {
      let match;
      while ((match = variableRegex.exec(template.subject)) !== null) {
        variables.add(match[1]);
      }
    }

    let bodyMatch;
    const bodyRegex = new RegExp(variableRegex);
    while ((bodyMatch = bodyRegex.exec(template.body)) !== null) {
      variables.add(bodyMatch[1]);
    }

    if (variables.size > 0) {
      setSelectedTemplate(template);
      // For simplicity, we'll just show the raw template
      // In a full implementation, you'd want a dialog to input variable values
      setPreviewData({
        subject: template.subject || undefined,
        body: template.body,
      });
      setPreviewDialogOpen(true);
    } else {
      setPreviewData({
        subject: template.subject || undefined,
        body: template.body,
      });
      setPreviewDialogOpen(true);
    }
    handleMenuClose();
  };

  const handleTemplateClick = (template: CommunicationTemplateResponse) => {
    if (onTemplateSelect) {
      onTemplateSelect(template);
    }
  };

  const handleAddVariable = () => {
    const newVar = prompt('Enter variable name (without {{ }}):');
    if (newVar && newVar.trim() && !templateVariables.includes(newVar.trim())) {
      setTemplateVariables([...templateVariables, newVar.trim()]);
    }
  };

  const handleRemoveVariable = (variable: string) => {
    setTemplateVariables(templateVariables.filter((v) => v !== variable));
  };

  return (
    <Box>
      {/* Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
        <Typography variant="h6">
          {type ? `${TEMPLATE_TYPE_LABELS[type]} Templates` : 'Communication Templates'}
        </Typography>
        {!readOnly && (
          <Button startIcon={<AddIcon />} onClick={handleOpenCreateDialog} size="small">
            New Template
          </Button>
        )}
      </Stack>

      {/* Templates List */}
      {templatesLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : templates.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <DescriptionIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
          <Typography variant="body2" color="text.secondary">
            No templates created yet
          </Typography>
        </Paper>
      ) : (
        <Grid2 container spacing={2}>
          {templates.map((template) => (
            <Grid2 key={template.id} size={{ xs: 12, sm: 6, md: 4, lg: 3 }}>
              <Paper
                sx={{
                  p: 2,
                  display: 'flex',
                  flexDirection: 'column',
                  height: '100%',
                  borderLeft: 4,
                  borderLeftColor: TEMPLATE_TYPE_COLORS[template.type],
                  cursor: onTemplateSelect ? 'pointer' : 'default',
                  position: 'relative',
                  opacity: template.is_active ? 1 : 0.6,
                  '&:hover': onTemplateSelect
                    ? {
                        boxShadow: 3,
                      }
                    : {},
                }}
                onClick={() => handleTemplateClick(template)}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="subtitle2" noWrap sx={{ fontWeight: 600 }}>
                      {template.name}
                    </Typography>
                    <Stack direction="row" spacing={0.5} alignItems="center" sx={{ mt: 0.5 }}>
                      <Chip
                        label={TEMPLATE_TYPE_LABELS[template.type]}
                        size="tiny"
                        sx={{
                          bgcolor: TEMPLATE_TYPE_COLORS[template.type],
                          color: 'white',
                          height: 20,
                          fontSize: '0.7rem',
                        }}
                      />
                      {template.category && (
                        <Chip
                          label={TEMPLATE_CATEGORY_LABELS[template.category]}
                          size="tiny"
                          variant="outlined"
                          sx={{ height: 20, fontSize: '0.7rem' }}
                        />
                      )}
                    </Stack>
                  </Box>
                  {!readOnly && (
                    <IconButton
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleMenuOpen(e, template);
                      }}
                      aria-label="Template options"
                    >
                      <MoreVertIcon fontSize="small" />
                    </IconButton>
                  )}
                </Box>

                {template.subject && (
                  <Typography variant="caption" color="text.secondary" noWrap sx={{ mb: 1 }}>
                    {template.subject}
                  </Typography>
                )}

                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{
                    mt: 'auto',
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden',
                    fontSize: '0.8rem',
                  }}
                >
                  {template.body}
                </Typography>

                <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mt: 1 }}>
                  {template.usage_count !== undefined && (
                    <Typography variant="caption" color="text.secondary">
                      {template.usage_count} {template.usage_count === 1 ? 'use' : 'uses'}
                    </Typography>
                  )}
                  {!template.is_active && (
                    <Chip label="Inactive" size="tiny" color="default" sx={{ height: 20, fontSize: '0.7rem' }} />
                  )}
                </Stack>
              </Paper>
            </Grid2>
          ))}
        </Grid2>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>{editMode ? 'Edit Template' : 'Create Template'}</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            fullWidth
            label="Template Name"
            value={templateName}
            onChange={(e) => setTemplateName(e.target.value)}
            sx={{ mt: 2 }}
            inputProps={{ maxLength: 100 }}
            helperText={`${templateName.length}/100 characters`}
            slotProps={{
              input: {
                'aria-label': 'Template name',
              },
            }}
          />

          <Grid2 container spacing={2} sx={{ mt: 1 }}>
            <Grid2 size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Type</InputLabel>
                <Select
                  value={templateType}
                  onChange={(e) => setTemplateType(e.target.value as TemplateType)}
                  label="Type"
                  disabled={editMode}
                >
                  <MenuItem value="email">Email</MenuItem>
                  <MenuItem value="sms">SMS</MenuItem>
                  <MenuItem value="in_system">In-System</MenuItem>
                </Select>
              </FormControl>
            </Grid2>
            <Grid2 size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Category</InputLabel>
                <Select
                  value={templateCategory}
                  onChange={(e) => setTemplateCategory(e.target.value as TemplateCategory)}
                  label="Category"
                >
                  <MenuItem value="outreach">Outreach</MenuItem>
                  <MenuItem value="interview">Interview</MenuItem>
                  <MenuItem value="rejection">Rejection</MenuItem>
                  <MenuItem value="offer">Offer</MenuItem>
                  <MenuItem value="follow_up">Follow Up</MenuItem>
                  <MenuItem value="other">Other</MenuItem>
                </Select>
              </FormControl>
            </Grid2>
          </Grid2>

          {templateType === 'email' && (
            <TextField
              fullWidth
              label="Subject"
              value={templateSubject}
              onChange={(e) => setTemplateSubject(e.target.value)}
              sx={{ mt: 2 }}
              inputProps={{ maxLength: 200 }}
              helperText="Use {{variable_name}} for dynamic content"
              slotProps={{
                input: {
                  'aria-label': 'Template subject',
                },
              }}
            />
          )}

          <TextField
            fullWidth
            label="Body"
            value={templateBody}
            onChange={(e) => setTemplateBody(e.target.value)}
            sx={{ mt: 2 }}
            multiline
            rows={6}
            required
            helperText="Use {{variable_name}} for dynamic content"
            slotProps={{
              input: {
                'aria-label': 'Template body',
              },
            }}
          />

          <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
            Variables
          </Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mb: 2 }}>
            {templateVariables.map((variable) => (
              <Chip
                key={variable}
                label={`{{${variable}}}`}
                onDelete={readOnly ? undefined : () => handleRemoveVariable(variable)}
                size="small"
                variant="outlined"
              />
            ))}
            {!readOnly && (
              <Chip label="+ Add Variable" onClick={handleAddVariable} size="small" sx={{ cursor: 'pointer' }} />
            )}
          </Stack>

          <TextField
            fullWidth
            label="Description"
            value={templateDescription}
            onChange={(e) => setTemplateDescription(e.target.value)}
            sx={{ mt: 1 }}
            multiline
            rows={2}
            inputProps={{ maxLength: 500 }}
            helperText={`${templateDescription.length}/500 characters`}
            slotProps={{
              input: {
                'aria-label': 'Template description',
              },
            }}
          />

          <FormControlLabel
            control={<Switch checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />}
            label="Active"
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleSaveTemplate}
            variant="contained"
            disabled={!templateName.trim() || !templateBody.trim() || createMutation.isPending || updateMutation.isPending}
          >
            {editMode ? 'Save' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Options Menu */}
      <Menu anchorEl={menuAnchor} open={Boolean(menuAnchor)} onClose={handleMenuClose}>
        <MenuItem
          onClick={() => {
            handleMenuClose();
            if (selectedTemplate) handleOpenEditDialog(selectedTemplate);
          }}
        >
          <EditIcon fontSize="small" sx={{ mr: 1 }} />
          Edit
        </MenuItem>
        <MenuItem
          onClick={() => {
            if (selectedTemplate) handlePreviewClick(selectedTemplate);
          }}
        >
          <PreviewIcon fontSize="small" sx={{ mr: 1 }} />
          Preview
        </MenuItem>
        <MenuItem onClick={handleDeleteClick} sx={{ color: 'error.main' }}>
          <DeleteIcon fontSize="small" sx={{ mr: 1 }} />
          Delete
        </MenuItem>
      </Menu>

      {/* Preview Dialog */}
      <Dialog open={previewDialogOpen} onClose={() => setPreviewDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Template Preview</DialogTitle>
        <DialogContent>
          {previewData && selectedTemplate && (
            <Box>
              <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                {selectedTemplate.name}
              </Typography>
              {previewData.subject && (
                <Paper sx={{ p: 2, mb: 2, bgcolor: 'grey.50' }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                    {previewData.subject}
                  </Typography>
                </Paper>
              )}
              <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                  {previewData.body}
                </Typography>
              </Paper>
              {selectedTemplate.variables && selectedTemplate.variables.length > 0 && (
                <Alert severity="info" sx={{ mt: 2 }}>
                  <Typography variant="caption">
                    Variables used: {selectedTemplate.variables.map((v) => `{{${v}}}`).join(', ')}
                  </Typography>
                </Alert>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPreviewDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Delete Template</DialogTitle>
        <DialogContent>
          {selectedTemplate && selectedTemplate.usage_count && selectedTemplate.usage_count > 0 ? (
            <Alert severity="warning" sx={{ mb: 2 }}>
              This template has been used {selectedTemplate.usage_count}{' '}
              {selectedTemplate.usage_count === 1 ? 'time' : 'times'}.
            </Alert>
          ) : null}
          <Typography variant="body1">Are you sure you want to delete "{selectedTemplate?.name}"?</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained" disabled={deleteMutation.isPending}>
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default CommunicationTemplates;
