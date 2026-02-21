/**
 * Resume Builder Page
 *
 * A comprehensive page for creating and editing resumes with:
 * - Template selection
 * - Full resume editor for all sections
 * - Live preview
 * - AI-powered improvement suggestions
 * - ATS optimization scoring
 * - Export to PDF/DOCX
 *
 * @module pages/jobs/ResumeBuilderPage
 */

import React, { useState, useCallback, useEffect, useMemo } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Stack,
  Button,
  CircularProgress,
  Alert,
  Chip,
  Divider,
  Tooltip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Snackbar,
  Tab,
  Tabs,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Save as SaveIcon,
  Download as DownloadIcon,
  AutoFixHigh as AIIcon,
  Assessment as ATSIcon,
  Visibility as PreviewIcon,
  Edit as EditIcon,
  Description as TemplateIcon,
  Add as AddIcon,
  ContentCopy as DuplicateIcon,
  Delete as DeleteIcon,
  MoreVert as MoreIcon,
} from '@mui/icons-material';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PageTransition } from '@components/mui/PageTransition';
import { LoadingState } from '@components/mui/LoadingState';
import { ErrorState } from '@components/mui/ErrorState';
import ResumeEditor from '@components/resume/ResumeEditor';
import ResumePreview from '@components/resume/ResumePreview';
import TemplateSelector from '@components/resume/TemplateSelector';
import AISuggestionsPanel, { type AISuggestionItem } from '@components/resume/AISuggestionsPanel';
import ATSScoreDisplay from '@components/resume/ATSScoreDisplay';
import { resumeBuilderClient, type ResumeListParams } from '@/api/resumeBuilder';
import type {
  BuiltResumeResponse,
  BuiltResumeCreate,
  BuiltResumeUpdate,
  ResumeContent,
  ExportFormat,
  ATSScoreResponse,
  AISuggestionsResponse,
} from '@/types/resumeBuilder';
import { createEmptyResumeContent } from '@/types/resumeBuilder';
import type { ResumeTemplateResponse } from '@/types/resume-templates';

/**
 * View mode for the page layout
 */
type ViewMode = 'edit' | 'preview' | 'ai' | 'ats' | 'templates';

/**
 * Panel tab interface for accessibility
 */
interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

/**
 * TabPanel component for accessible tab content
 */
function TabPanel({ children, value, index }: TabPanelProps) {
  return (
    <div
      role="tabpanel"
      id={`resume-builder-tabpanel-${index}`}
      aria-labelledby={`resume-builder-tab-${index}`}
      hidden={value !== index}
    >
      {value === index && <Box sx={{ py: 2 }}>{children}</Box>}
    </div>
  );
}

/**
 * Accessibility props for tabs
 */
function a11yProps(index: number) {
  return {
    id: `resume-builder-tab-${index}`,
    'aria-controls': `resume-builder-tabpanel-${index}`,
  };
}

/**
 * ResumeBuilderPage Component
 *
 * Main page for the resume builder feature. Provides a comprehensive interface
 * for creating, editing, and optimizing resumes with AI assistance.
 */
const ResumeBuilderPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // State management
  const [currentView, setCurrentView] = useState<ViewMode>('edit');
  const [content, setContent] = useState<ResumeContent>(createEmptyResumeContent());
  const [title, setTitle] = useState<string>('Untitled Resume');
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | undefined>();
  const [isDraft, setIsDraft] = useState<boolean>(true);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState<boolean>(false);
  const [snackbarMessage, setSnackbarMessage] = useState<string | null>(null);
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error' | 'info'>('info');
  const [showDeleteDialog, setShowDeleteDialog] = useState<boolean>(false);
  const [showExportDialog, setShowExportDialog] = useState<boolean>(false);
  const [exportFormat, setExportFormat] = useState<ExportFormat>('pdf');

  // Derived state
  const isNewResume = !id;

  // Load existing resume if editing
  const {
    data: resumeData,
    isLoading: isLoadingResume,
    error: resumeError,
  } = useQuery({
    queryKey: ['resume', id],
    queryFn: () => resumeBuilderClient.getResume(id!),
    enabled: !!id,
  });

  // Load templates
  const {
    data: templatesData,
    isLoading: isLoadingTemplates,
  } = useQuery({
    queryKey: ['resume-templates'],
    queryFn: () => resumeBuilderClient.getTemplates(),
  });

  // Load AI suggestions
  const {
    data: aiSuggestionsData,
    isLoading: isLoadingAiSuggestions,
    error: aiSuggestionsError,
    refetch: refetchAiSuggestions,
  } = useQuery({
    queryKey: ['resume-ai-suggestions', id],
    queryFn: () => resumeBuilderClient.getAISuggestions(id!),
    enabled: !!id && currentView === 'ai',
  });

  // Load ATS score
  const {
    data: atsScoreData,
    isLoading: isLoadingAtsScore,
    error: atsScoreError,
    refetch: refetchAtsScore,
  } = useQuery({
    queryKey: ['resume-ats-score', id],
    queryFn: () => resumeBuilderClient.calculateATSScore(id!),
    enabled: !!id && currentView === 'ats',
  });

  // Create resume mutation
  const createMutation = useMutation({
    mutationFn: (data: BuiltResumeCreate) => resumeBuilderClient.createResume(data),
    onSuccess: (newResume) => {
      setSnackbarMessage('Resume created successfully!');
      setSnackbarSeverity('success');
      setHasUnsavedChanges(false);
      navigate(`/jobs/resume-builder/${newResume.id}`, { replace: true });
    },
    onError: (error: { detail?: string }) => {
      setSnackbarMessage(error.detail || 'Failed to create resume');
      setSnackbarSeverity('error');
    },
  });

  // Update resume mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: BuiltResumeUpdate }) =>
      resumeBuilderClient.updateResume(id, data),
    onSuccess: () => {
      setSnackbarMessage('Resume saved successfully!');
      setSnackbarSeverity('success');
      setHasUnsavedChanges(false);
      queryClient.invalidateQueries({ queryKey: ['resume', id] });
    },
    onError: (error: { detail?: string }) => {
      setSnackbarMessage(error.detail || 'Failed to save resume');
      setSnackbarSeverity('error');
    },
  });

  // Delete resume mutation
  const deleteMutation = useMutation({
    mutationFn: (resumeId: string) => resumeBuilderClient.deleteResume(resumeId),
    onSuccess: () => {
      setSnackbarMessage('Resume deleted successfully!');
      setSnackbarSeverity('success');
      navigate('/jobs/resumes');
    },
    onError: (error: { detail?: string }) => {
      setSnackbarMessage(error.detail || 'Failed to delete resume');
      setSnackbarSeverity('error');
    },
  });

  // Export mutation
  const exportMutation = useMutation({
    mutationFn: ({ id, format }: { id: string; format: ExportFormat }) =>
      resumeBuilderClient.exportResume(id, format),
    onSuccess: (result) => {
      window.open(result.download_url, '_blank');
      setSnackbarMessage(`${exportFormat.toUpperCase()} export started!`);
      setSnackbarSeverity('success');
      setShowExportDialog(false);
    },
    onError: (error: { detail?: string }) => {
      setSnackbarMessage(error.detail || 'Failed to export resume');
      setSnackbarSeverity('error');
    },
  });

  // Apply suggestion mutation
  const applySuggestionMutation = useMutation({
    mutationFn: ({ id, suggestionId }: { id: string; suggestionId: string }) =>
      resumeBuilderClient.applySuggestion(id, { suggestion_id: suggestionId }),
    onSuccess: (updatedResume) => {
      setContent(updatedResume.content);
      setSnackbarMessage('Suggestion applied successfully!');
      setSnackbarSeverity('success');
      queryClient.invalidateQueries({ queryKey: ['resume-ai-suggestions', id] });
    },
    onError: (error: { detail?: string }) => {
      setSnackbarMessage(error.detail || 'Failed to apply suggestion');
      setSnackbarSeverity('error');
    },
  });

  // Initialize content from loaded resume
  useEffect(() => {
    if (resumeData) {
      setContent(resumeData.content || createEmptyResumeContent());
      setTitle(resumeData.title || 'Untitled Resume');
      setSelectedTemplateId(resumeData.template_id || undefined);
      setIsDraft(resumeData.is_draft ?? true);
    }
  }, [resumeData]);

  // Sync URL params with view
  useEffect(() => {
    const viewParam = searchParams.get('view') as ViewMode;
    if (viewParam && ['edit', 'preview', 'ai', 'ats', 'templates'].includes(viewParam)) {
      setCurrentView(viewParam);
    }
  }, [searchParams]);

  // Handle content changes
  const handleContentChange = useCallback((newContent: ResumeContent) => {
    setContent(newContent);
    setHasUnsavedChanges(true);
  }, []);

  // Handle template selection
  const handleTemplateSelect = useCallback((template: ResumeTemplateResponse) => {
    setSelectedTemplateId(template.id);
    setHasUnsavedChanges(true);
  }, []);

  // Handle save
  const handleSave = useCallback(async () => {
    const data: BuiltResumeCreate | BuiltResumeUpdate = {
      title,
      content,
      template_id: selectedTemplateId,
      is_draft: isDraft,
    };

    if (isNewResume) {
      await createMutation.mutateAsync(data as BuiltResumeCreate);
    } else {
      await updateMutation.mutateAsync({ id: id!, data: data as BuiltResumeUpdate });
    }
  }, [id, isNewResume, title, content, selectedTemplateId, isDraft, createMutation, updateMutation]);

  // Handle delete
  const handleDelete = useCallback(async () => {
    if (id) {
      await deleteMutation.mutateAsync(id);
      setShowDeleteDialog(false);
    }
  }, [id, deleteMutation]);

  // Handle export
  const handleExport = useCallback(async () => {
    if (id) {
      await exportMutation.mutateAsync({ id, format: exportFormat });
    }
  }, [id, exportFormat, exportMutation]);

  // Handle apply AI suggestion
  const handleApplySuggestion = useCallback((suggestion: AISuggestionItem) => {
    if (id && suggestion.id) {
      applySuggestionMutation.mutate({ id, suggestionId: suggestion.id });
    }
  }, [id, applySuggestionMutation]);

  // Handle view change
  const handleViewChange = useCallback((view: ViewMode) => {
    setCurrentView(view);
    setSearchParams({ view });
  }, [setSearchParams]);

  // Handle tab change
  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    const views: ViewMode[] = ['edit', 'preview', 'ai', 'ats', 'templates'];
    handleViewChange(views[newValue]);
  };

  // Get current tab index
  const currentTabIndex = useMemo(() => {
    const views: ViewMode[] = ['edit', 'preview', 'ai', 'ats', 'templates'];
    return views.indexOf(currentView);
  }, [currentView]);

  // Templates list
  const templates = templatesData?.items || [];

  // Transform AI suggestions for the panel
  const transformedAiSuggestions = useMemo(() => {
    if (!aiSuggestionsData) return null;
    return {
      resume_id: aiSuggestionsData.resume_id,
      ai_score: aiSuggestionsData.ats_score_potential || 0,
      suggestions: (aiSuggestionsData.suggestions || []).map((s) => ({
        ...s,
        id: s.id,
        priority: s.priority || 'medium',
        category: s.category || 'content',
        title: s.title,
        description: s.description,
        recommendation: s.recommendation,
        current_state: s.current_state,
      })) as AISuggestionItem[],
      total_suggestions: aiSuggestionsData.suggestions?.length || 0,
    };
  }, [aiSuggestionsData]);

  // Loading state
  if (isLoadingResume && id) {
    return (
      <PageTransition>
        <Container maxWidth="xl" sx={{ py: 4 }}>
          <LoadingState message="Loading resume..." />
        </Container>
      </PageTransition>
    );
  }

  // Error state
  if (resumeError && id) {
    return (
      <PageTransition>
        <Container maxWidth="xl" sx={{ py: 4 }}>
          <ErrorState
            title="Error Loading Resume"
            message={resumeError.detail || 'Failed to load resume data'}
            onRetry={() => queryClient.invalidateQueries({ queryKey: ['resume', id] })}
          />
        </Container>
      </PageTransition>
    );
  }

  const isSaving = createMutation.isPending || updateMutation.isPending;

  return (
    <PageTransition>
      <Container maxWidth="xl" sx={{ py: 4 }}>
        {/* Header Section */}
        <Stack
          direction={{ xs: 'column', sm: 'row' }}
          justifyContent="space-between"
          alignItems={{ xs: 'flex-start', sm: 'center' }}
          spacing={2}
          sx={{ mb: 3 }}
        >
          <Stack direction="row" spacing={2} alignItems="center">
            <Tooltip title="Back to Resumes">
              <IconButton onClick={() => navigate('/jobs/resumes')}>
                <ArrowBackIcon />
              </IconButton>
            </Tooltip>
            <Box>
              <TextField
                value={title}
                onChange={(e) => {
                  setTitle(e.target.value);
                  setHasUnsavedChanges(true);
                }}
                variant="standard"
                size="small"
                placeholder="Untitled Resume"
                sx={{
                  '& .MuiInputBase-input': {
                    fontSize: '1.5rem',
                    fontWeight: 700,
                  },
                }}
              />
              <Stack direction="row" spacing={1} alignItems="center" sx={{ mt: 0.5 }}>
                <Chip
                  label={isDraft ? 'Draft' : 'Published'}
                  size="small"
                  color={isDraft ? 'warning' : 'success'}
                  variant="outlined"
                />
                {hasUnsavedChanges && (
                  <Chip
                    label="Unsaved changes"
                    size="small"
                    color="info"
                    variant="outlined"
                  />
                )}
                {resumeData?.version && (
                  <Typography variant="caption" color="text.secondary">
                    Version {resumeData.version}
                  </Typography>
                )}
              </Stack>
            </Box>
          </Stack>

          {/* Action Buttons */}
          <Stack direction="row" spacing={1}>
            {!isNewResume && (
              <>
                <Tooltip title="Export">
                  <Button
                    variant="outlined"
                    startIcon={<DownloadIcon />}
                    onClick={() => setShowExportDialog(true)}
                    disabled={isSaving}
                  >
                    Export
                  </Button>
                </Tooltip>
                <Tooltip title="Delete">
                  <IconButton
                    color="error"
                    onClick={() => setShowDeleteDialog(true)}
                    disabled={isSaving}
                  >
                    <DeleteIcon />
                  </IconButton>
                </Tooltip>
              </>
            )}
            <Button
              variant="contained"
              startIcon={isSaving ? <CircularProgress size={16} /> : <SaveIcon />}
              onClick={handleSave}
              disabled={isSaving}
            >
              {isSaving ? 'Saving...' : 'Save'}
            </Button>
          </Stack>
        </Stack>

        {/* Main Content */}
        <Paper sx={{ width: '100%' }}>
          {/* Navigation Tabs */}
          <Tabs
            value={currentTabIndex}
            onChange={handleTabChange}
            variant={isMobile ? 'scrollable' : 'fullWidth'}
            scrollButtons={isMobile ? 'auto' : undefined}
            sx={{
              borderBottom: 1,
              borderColor: 'divider',
              px: 2,
            }}
          >
            <Tab
              icon={<EditIcon />}
              label="Edit"
              {...a11yProps(0)}
              sx={{ minHeight: 64 }}
            />
            <Tab
              icon={<PreviewIcon />}
              label="Preview"
              {...a11yProps(1)}
              sx={{ minHeight: 64 }}
            />
            <Tab
              icon={<AIIcon />}
              label="AI Suggestions"
              {...a11yProps(2)}
              sx={{ minHeight: 64 }}
              disabled={isNewResume}
            />
            <Tab
              icon={<ATSIcon />}
              label="ATS Score"
              {...a11yProps(3)}
              sx={{ minHeight: 64 }}
              disabled={isNewResume}
            />
            <Tab
              icon={<TemplateIcon />}
              label="Templates"
              {...a11yProps(4)}
              sx={{ minHeight: 64 }}
            />
          </Tabs>

          {/* Edit Tab */}
          <TabPanel value={currentTabIndex} index={0}>
            <Box sx={{ px: 2 }}>
              <ResumeEditor
                initialContent={content}
                onChange={handleContentChange}
                onSave={async (newContent) => {
                  handleContentChange(newContent);
                  await handleSave();
                }}
                saving={isSaving}
                title="Resume Content"
              />
            </Box>
          </TabPanel>

          {/* Preview Tab */}
          <TabPanel value={currentTabIndex} index={1}>
            <Box sx={{ px: 2 }}>
              <ResumePreview
                content={content}
                loading={false}
                title="Live Preview"
                showZoomControls
                showPrintButton
                templateStyle="modern"
              />
            </Box>
          </TabPanel>

          {/* AI Suggestions Tab */}
          <TabPanel value={currentTabIndex} index={2}>
            <Box sx={{ px: 2 }}>
              <AISuggestionsPanel
                suggestionsData={transformedAiSuggestions}
                loading={isLoadingAiSuggestions}
                error={aiSuggestionsError?.detail || null}
                title="AI Improvement Suggestions"
                onApplySuggestion={handleApplySuggestion}
                onRegenerate={() => refetchAiSuggestions()}
                showRegenerate
                disabled={isSaving}
              />
            </Box>
          </TabPanel>

          {/* ATS Score Tab */}
          <TabPanel value={currentTabIndex} index={3}>
            <Box sx={{ px: 2 }}>
              <ATSScoreDisplay
                scoreData={atsScoreData || null}
                loading={isLoadingAtsScore}
                error={atsScoreError?.detail || null}
                title="ATS Optimization Score"
                showRecalculate
                onRecalculate={() => refetchAtsScore()}
                disabled={isSaving}
                showDetails
              />
            </Box>
          </TabPanel>

          {/* Templates Tab */}
          <TabPanel value={currentTabIndex} index={4}>
            <Box sx={{ px: 2 }}>
              <TemplateSelector
                templates={templates}
                selectedTemplateId={selectedTemplateId}
                onSelectTemplate={handleTemplateSelect}
                loading={isLoadingTemplates}
                columns={3}
                showAtsBadge
                disabled={isSaving}
              />
            </Box>
          </TabPanel>
        </Paper>

        {/* Unsaved Changes Warning */}
        {hasUnsavedChanges && (
          <Alert severity="warning" sx={{ mt: 2 }}>
            You have unsaved changes. Don't forget to save your resume!
          </Alert>
        )}

        {/* Delete Confirmation Dialog */}
        <Dialog open={showDeleteDialog} onClose={() => setShowDeleteDialog(false)}>
          <DialogTitle>Delete Resume?</DialogTitle>
          <DialogContent>
            <Typography>
              Are you sure you want to delete "{title}"? This action cannot be undone.
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowDeleteDialog(false)}>Cancel</Button>
            <Button
              color="error"
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
              startIcon={deleteMutation.isPending ? <CircularProgress size={16} /> : <DeleteIcon />}
            >
              Delete
            </Button>
          </DialogActions>
        </Dialog>

        {/* Export Dialog */}
        <Dialog open={showExportDialog} onClose={() => setShowExportDialog(false)}>
          <DialogTitle>Export Resume</DialogTitle>
          <DialogContent>
            <Typography gutterBottom>
              Choose a format to export your resume:
            </Typography>
            <FormControl fullWidth sx={{ mt: 2 }}>
              <InputLabel>Format</InputLabel>
              <Select
                value={exportFormat}
                onChange={(e) => setExportFormat(e.target.value as ExportFormat)}
                label="Format"
              >
                <MenuItem value="pdf">PDF - Best for applications</MenuItem>
                <MenuItem value="docx">DOCX - Editable format</MenuItem>
                <MenuItem value="json">JSON - Data backup</MenuItem>
              </Select>
            </FormControl>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowExportDialog(false)}>Cancel</Button>
            <Button
              variant="contained"
              onClick={handleExport}
              disabled={exportMutation.isPending}
              startIcon={exportMutation.isPending ? <CircularProgress size={16} /> : <DownloadIcon />}
            >
              Export
            </Button>
          </DialogActions>
        </Dialog>

        {/* Snackbar for notifications */}
        <Snackbar
          open={!!snackbarMessage}
          autoHideDuration={5000}
          onClose={() => setSnackbarMessage(null)}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        >
          <Alert
            onClose={() => setSnackbarMessage(null)}
            severity={snackbarSeverity}
            sx={{ width: '100%' }}
          >
            {snackbarMessage}
          </Alert>
        </Snackbar>
      </Container>
    </PageTransition>
  );
};

export default ResumeBuilderPage;
export { ResumeBuilderPage };
