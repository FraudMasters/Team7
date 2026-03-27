/**
 * Feedback Templates Page Component
 *
 * Manage feedback notification templates with the visual template builder.
 */

import { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Stack,
  Dialog,
  DialogContent,
  IconButton,
  Grid2,
  Paper,
  Alert,
  CircularProgress,
  Menu,
  MenuItem,
  Chip,
  Card,
  CardContent,
  CardActions,
  Container,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Close as CloseIcon,
  MoreVert as MoreVertIcon,
  Preview as PreviewIcon,
  Email as EmailIcon,
  Sms as SmsIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notificationTemplatesClient } from '../api/notificationTemplates';
import type {
  NotificationTemplateResponse,
  NotificationTemplateType,
} from '../api/notificationTemplates';
import { TemplateBuilder } from '../components/TemplateBuilder/TemplateBuilder';

const TEMPLATE_TYPE_LABELS: Record<NotificationTemplateType, string> = {
  email: 'Email',
  sms: 'SMS',
};

const TEMPLATE_TYPE_COLORS: Record<NotificationTemplateType, string> = {
  email: '#1976D2',
  sms: '#7B1FA2',
};

const TEMPLATE_TYPE_ICONS: Record<NotificationTemplateType, typeof EmailIcon> = {
  email: EmailIcon,
  sms: SmsIcon,
};

const FeedbackTemplatesPage: React.FC = () => {
  const queryClient = useQueryClient();

  const [builderDialogOpen, setBuilderDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<NotificationTemplateResponse | null>(null);
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const [menuTemplateId, setMenuTemplateId] = useState<string | null>(null);

  // Fetch feedback templates
  const { data: templatesData, isLoading: templatesLoading } = useQuery({
    queryKey: ['notification-templates', 'feedback'],
    queryFn: async () => {
      return await notificationTemplatesClient.listTemplates({
        category: 'feedback',
        limit: 100,
        offset: 0,
      });
    },
  });

  const templates = templatesData?.templates || [];

  // Delete template mutation
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await notificationTemplatesClient.deleteTemplate(id);
    },
    onSuccess: () => {
      setDeleteDialogOpen(false);
      setSelectedTemplate(null);
      queryClient.invalidateQueries({ queryKey: ['notification-templates'] });
    },
  });

  const handleCreateNew = () => {
    setSelectedTemplate(null);
    setBuilderDialogOpen(true);
  };

  const handleEdit = (template: NotificationTemplateResponse) => {
    setSelectedTemplate(template);
    setBuilderDialogOpen(true);
    setMenuAnchor(null);
  };

  const handleDeleteClick = (template: NotificationTemplateResponse) => {
    setSelectedTemplate(template);
    setDeleteDialogOpen(true);
    setMenuAnchor(null);
  };

  const handleDeleteConfirm = () => {
    if (selectedTemplate) {
      deleteMutation.mutate(selectedTemplate.id);
    }
  };

  const handleBuilderSave = (templateId: string) => {
    setBuilderDialogOpen(false);
    setSelectedTemplate(null);
  };

  const handleBuilderCancel = () => {
    setBuilderDialogOpen(false);
    setSelectedTemplate(null);
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, templateId: string) => {
    setMenuAnchor(event.currentTarget);
    setMenuTemplateId(templateId);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
    setMenuTemplateId(null);
  };

  const getTemplateForMenu = () => {
    return templates.find(t => t.id === menuTemplateId) || null;
  };

  return (
    <Container maxWidth="xl">
      <Box sx={{ py: 4 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Box>
              <Typography variant="h4" component="h1" fontWeight={700} gutterBottom>
                Feedback Templates
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Create and manage notification templates for candidate feedback
              </Typography>
            </Box>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleCreateNew}
              size="large"
            >
              Create Template
            </Button>
          </Stack>
        </Box>

        {/* Templates Grid */}
        {templatesLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
            <CircularProgress />
          </Box>
        ) : templates.length === 0 ? (
          <Paper sx={{ p: 6, textAlign: 'center' }}>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No feedback templates yet
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Create your first template to get started
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleCreateNew}
            >
              Create Template
            </Button>
          </Paper>
        ) : (
          <Grid2 container spacing={3}>
            {templates.map((template) => {
              const TypeIcon = TEMPLATE_TYPE_ICONS[template.type];
              return (
                <Grid2 key={template.id} size={{ xs: 12, sm: 6, md: 4 }}>
                  <Card
                    sx={{
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      border: 1,
                      borderColor: 'divider',
                      '&:hover': {
                        borderColor: 'primary.main',
                        boxShadow: 2,
                      },
                    }}
                  >
                    <CardContent sx={{ flex: 1 }}>
                      <Stack direction="row" justifyContent="space-between" alignItems="flex-start" sx={{ mb: 2 }}>
                        <Box sx={{ flex: 1, mr: 1 }}>
                          <Typography variant="h6" component="h2" gutterBottom>
                            {template.name}
                          </Typography>
                        </Box>
                        <IconButton
                          size="small"
                          onClick={(e) => handleMenuOpen(e, template.id)}
                        >
                          <MoreVertIcon />
                        </IconButton>
                      </Stack>

                      <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
                        <Chip
                          icon={<TypeIcon />}
                          label={TEMPLATE_TYPE_LABELS[template.type]}
                          size="small"
                          sx={{
                            bgcolor: TEMPLATE_TYPE_COLORS[template.type] + '20',
                            color: TEMPLATE_TYPE_COLORS[template.type],
                            fontWeight: 600,
                          }}
                        />
                        {!template.is_active && (
                          <Chip
                            label="Inactive"
                            size="small"
                            color="default"
                          />
                        )}
                      </Stack>

                      {template.description && (
                        <Typography
                          variant="body2"
                          color="text.secondary"
                          sx={{
                            mb: 2,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            display: '-webkit-box',
                            WebkitLineClamp: 2,
                            WebkitBoxOrient: 'vertical',
                          }}
                        >
                          {template.description}
                        </Typography>
                      )}

                      {template.pipeline_stage && (
                        <Chip
                          label={template.pipeline_stage.replace(/_/g, ' ').toUpperCase()}
                          size="small"
                          variant="outlined"
                        />
                      )}

                      {template.variables && template.variables.length > 0 && (
                        <Box sx={{ mt: 2 }}>
                          <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                            Variables: {template.variables.slice(0, 3).map(v => `{{${v}}}`).join(', ')}
                            {template.variables.length > 3 && ` +${template.variables.length - 3} more`}
                          </Typography>
                        </Box>
                      )}
                    </CardContent>

                    <CardActions sx={{ px: 2, pb: 2 }}>
                      <Button
                        size="small"
                        startIcon={<EditIcon />}
                        onClick={() => handleEdit(template)}
                      >
                        Edit
                      </Button>
                      <Button
                        size="small"
                        color="error"
                        startIcon={<DeleteIcon />}
                        onClick={() => handleDeleteClick(template)}
                      >
                        Delete
                      </Button>
                    </CardActions>
                  </Card>
                </Grid2>
              );
            })}
          </Grid2>
        )}

        {/* Template Menu */}
        <Menu
          anchorEl={menuAnchor}
          open={Boolean(menuAnchor)}
          onClose={handleMenuClose}
        >
          <MenuItem
            onClick={() => {
              const template = getTemplateForMenu();
              if (template) handleEdit(template);
            }}
          >
            <EditIcon fontSize="small" sx={{ mr: 1 }} />
            Edit
          </MenuItem>
          <MenuItem
            onClick={() => {
              const template = getTemplateForMenu();
              if (template) handleDeleteClick(template);
            }}
          >
            <DeleteIcon fontSize="small" sx={{ mr: 1 }} />
            Delete
          </MenuItem>
        </Menu>

        {/* Template Builder Dialog */}
        <Dialog
          open={builderDialogOpen}
          onClose={handleBuilderCancel}
          maxWidth="xl"
          fullWidth
          fullScreen
        >
          <Box sx={{ position: 'relative', height: '100vh' }}>
            <IconButton
              onClick={handleBuilderCancel}
              sx={{
                position: 'absolute',
                right: 8,
                top: 8,
                zIndex: 1,
              }}
            >
              <CloseIcon />
            </IconButton>
            <TemplateBuilder
              templateId={selectedTemplate?.id}
              initialType={selectedTemplate?.type || 'email'}
              onSave={handleBuilderSave}
              onCancel={handleBuilderCancel}
            />
          </Box>
        </Dialog>

        {/* Delete Confirmation Dialog */}
        <Dialog
          open={deleteDialogOpen}
          onClose={() => setDeleteDialogOpen(false)}
          maxWidth="sm"
          fullWidth
        >
          <DialogContent>
            <Stack spacing={2}>
              <Typography variant="h6">Delete Template?</Typography>
              <Typography variant="body2" color="text.secondary">
                Are you sure you want to delete "{selectedTemplate?.name}"? This action cannot be undone.
              </Typography>
              {deleteMutation.isError && (
                <Alert severity="error">
                  Failed to delete template. Please try again.
                </Alert>
              )}
              <Stack direction="row" spacing={2} justifyContent="flex-end">
                <Button
                  onClick={() => setDeleteDialogOpen(false)}
                  disabled={deleteMutation.isPending}
                >
                  Cancel
                </Button>
                <Button
                  variant="contained"
                  color="error"
                  onClick={handleDeleteConfirm}
                  disabled={deleteMutation.isPending}
                  startIcon={deleteMutation.isPending ? <CircularProgress size={16} /> : <DeleteIcon />}
                >
                  {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
                </Button>
              </Stack>
            </Stack>
          </DialogContent>
        </Dialog>
      </Box>
    </Container>
  );
};

export default FeedbackTemplatesPage;
