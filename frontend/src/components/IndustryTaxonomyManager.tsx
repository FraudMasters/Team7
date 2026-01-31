import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import PublicTaxonomyBrowser from './PublicTaxonomyBrowser';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Alert,
  AlertTitle,
  Stack,
  Divider,
  Grid,
  Card,
  CardContent,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  CircularProgress,
  IconButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tab,
  Tabs,
  Menu,
  LinearProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Close as CloseIcon,
  History as HistoryIcon,
  Public as PublicIcon,
  CloudUpload as CloudUploadIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  FileDownload as FileDownloadIcon,
} from '@mui/icons-material';

/**
 * Individual skill taxonomy entry interface
 */
interface SkillTaxonomyEntry {
  skill_name: string;
  variants: string[];
  context?: string;
  is_active: boolean;
}

/**
 * Skill taxonomy response from backend
 */
interface SkillTaxonomy {
  id: string;
  industry: string;
  skill_name: string;
  variants: string[];
  context?: string;
  extra_metadata?: Record<string, unknown>;
  is_active: boolean;
  is_public: boolean;
  view_count: number;
  use_count: number;
  last_used_at?: string;
  created_at: string;
  updated_at: string;
}

/**
 * List response from backend
 */
interface SkillTaxonomyListResponse {
  industry: string;
  skills: SkillTaxonomy[];
  total_count: number;
}

/**
 * Form data for creating/editing skill taxonomies
 */
interface TaxonomyFormData {
  skill_name: string;
  variants: string;
  context: string;
  is_active: boolean;
}

/**
 * Taxonomy version response from backend
 */
interface TaxonomyVersion {
  id: string;
  industry: string;
  skill_name: string;
  context?: string;
  variants: string[];
  extra_metadata?: Record<string, unknown>;
  is_active: boolean;
  version: number;
  previous_version_id?: string;
  is_latest: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Version list response from backend
 */
interface TaxonomyVersionListResponse {
  taxonomy_id: string;
  skill_name: string;
  industry: string;
  versions: TaxonomyVersion[];
  total_count: number;
}

/**
 * Industry taxonomy manager component props
 */
interface IndustryTaxonomyManagerProps {
  /** Organization ID to manage taxonomies for */
  organizationId?: string;
  /** API endpoint URL for skill taxonomies */
  apiUrl?: string;
}

/**
 * IndustryTaxonomyManager Component
 *
 * Provides a comprehensive admin interface for managing industry-specific
 * skill taxonomies. Features include:
 * - List all skill taxonomies for selected industry
 * - Create new skill taxonomy entries
 * - Edit existing taxonomy entries
 * - Delete individual or all taxonomies in an industry
 * - Toggle active/inactive status
 * - Industry selector dropdown
 * - Real-time updates with optimistic UI
 *
 * @example
 * ```tsx
 * <IndustryTaxonomyManager organizationId="org123" />
 * ```
 */
const IndustryTaxonomyManager: React.FC<IndustryTaxonomyManagerProps> = ({
  organizationId = 'default',
  apiUrl = 'http://localhost:8000/api/skill-taxonomies',
}) => {
  const { t } = useTranslation();
  const [currentTab, setCurrentTab] = useState<'manage' | 'browse'>('manage');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [taxonomies, setTaxonomies] = useState<SkillTaxonomy[]>([]);
  const [selectedIndustry, setSelectedIndustry] = useState<string>('tech');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingTaxonomy, setEditingTaxonomy] = useState<SkillTaxonomy | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [taxonomyToDelete, setTaxonomyToDelete] = useState<SkillTaxonomy | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [publishingDialogOpen, setPublishingDialogOpen] = useState(false);
  const [taxonomyToPublish, setTaxonomyToPublish] = useState<SkillTaxonomy | null>(null);
  const [togglingPublic, setTogglingPublic] = useState(false);

  // Version history state
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [selectedTaxonomyForHistory, setSelectedTaxonomyForHistory] = useState<SkillTaxonomy | null>(null);
  const [versions, setVersions] = useState<TaxonomyVersion[]>([]);
  const [loadingVersions, setLoadingVersions] = useState(false);
  const [rollingBack, setRollingBack] = useState(false);

  // Import/Export state
  const [exportMenuAnchor, setExportMenuAnchor] = useState<null | HTMLElement>(null);
  const [importDialogOpen, setImportDialogOpen] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [importProgress, setImportProgress] = useState(0);
  const [importError, setImportError] = useState<string | null>(null);
  const [importSuccess, setImportSuccess] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Form state
  const [formData, setFormData] = useState<TaxonomyFormData>({
    skill_name: '',
    variants: '',
    context: '',
    is_active: true,
  });

  // Available industries
  const industries = [
    'it',
    'tech',
    'healthcare',
    'finance',
    'marketing',
    'manufacturing',
    'sales',
    'design',
  ];

  /**
   * Fetch skill taxonomies from backend
   */
  const fetchTaxonomies = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiUrl}/?industry=${selectedIndustry}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch taxonomies: ${response.statusText}`);
      }

      const result: SkillTaxonomyListResponse = await response.json();
      setTaxonomies(result.skills || []);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : t('industryTaxonomy.errors.failedToLoad');
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Load predefined IT taxonomy
   */
  const loadITTaxonomy = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiUrl}/load/it`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to load IT taxonomy: ${response.statusText}`);
      }

      const result = await response.json();

      // Refresh taxonomies after loading
      await fetchTaxonomies();

      // Show success message (could use a snackbar in a full implementation)
      alert(`Loaded ${result.loaded_count} IT skills successfully!`);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load IT taxonomy';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedIndustry) {
      fetchTaxonomies();
    }
  }, [selectedIndustry]);

  /**
   * Handle industry change
   */
  const handleIndustryChange = (_event: React.SyntheticEvent, newValue: string) => {
    setSelectedIndustry(newValue);
  };

  /**
   * Open create dialog
   */
  const handleCreate = () => {
    setEditingTaxonomy(null);
    setFormData({
      skill_name: '',
      variants: '',
      context: '',
      is_active: true,
    });
    setDialogOpen(true);
  };

  /**
   * Open edit dialog
   */
  const handleEdit = (taxonomy: SkillTaxonomy) => {
    setEditingTaxonomy(taxonomy);
    setFormData({
      skill_name: taxonomy.skill_name,
      variants: taxonomy.variants.join(', '),
      context: taxonomy.context || '',
      is_active: taxonomy.is_active,
    });
    setDialogOpen(true);
  };

  /**
   * Open delete confirmation dialog
   */
  const handleDeleteClick = (taxonomy: SkillTaxonomy) => {
    setTaxonomyToDelete(taxonomy);
    setDeleteDialogOpen(true);
  };

  /**
   * Confirm delete
   */
  const handleDeleteConfirm = async () => {
    if (!taxonomyToDelete) return;

    setSubmitting(true);
    try {
      const response = await fetch(`${apiUrl}/${taxonomyToDelete.id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`${t('industryTaxonomy.errors.failedToDelete')}: ${response.statusText}`);
      }

      // Optimistic update
      setTaxonomies(taxonomies.filter((t) => t.id !== taxonomyToDelete.id));
      setDeleteDialogOpen(false);
      setTaxonomyToDelete(null);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : t('industryTaxonomy.errors.failedToDelete');
      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  /**
   * Submit form (create or update)
   */
  const handleSubmit = async () => {
    setSubmitting(true);
    setError(null);

    try {
      // Parse variants
      const variantsArray = formData.variants
        .split(',')
        .map((s) => s.trim())
        .filter((s) => s.length > 0);

      if (variantsArray.length === 0) {
        throw new Error(t('industryTaxonomy.dialog.atLeastOneVariantError'));
      }

      if (editingTaxonomy) {
        // Update existing taxonomy
        const response = await fetch(`${apiUrl}/${editingTaxonomy.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            skill_name: formData.skill_name,
            variants: variantsArray,
            context: formData.context || null,
            is_active: formData.is_active,
          }),
        });

        if (!response.ok) {
          throw new Error(`${t('industryTaxonomy.errors.failedToUpdate')}: ${response.statusText}`);
        }

        const updated: SkillTaxonomy = await response.json();
        setTaxonomies(taxonomies.map((t) => (t.id === updated.id ? updated : t)));
      } else {
        // Create new taxonomy
        const response = await fetch(apiUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            industry: selectedIndustry,
            skills: [
              {
                name: formData.skill_name,
                variants: variantsArray,
                context: formData.context || null,
                is_active: formData.is_active,
              },
            ],
          }),
        });

        if (!response.ok) {
          throw new Error(`${t('industryTaxonomy.errors.failedToCreate')}: ${response.statusText}`);
        }

        const result: SkillTaxonomyListResponse = await response.json();
        if (result.skills && result.skills.length > 0) {
          setTaxonomies([...taxonomies, ...result.skills]);
        }
      }

      setDialogOpen(false);
      setFormData({
        skill_name: '',
        variants: '',
        context: '',
        is_active: true,
      });
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : t('industryTaxonomy.errors.failedToCreate');
      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  /**
   * Get context color for display
   */
  const getContextColor = (context?: string) => {
    switch (context) {
      case 'web_framework':
        return 'primary' as const;
      case 'language':
        return 'success' as const;
      case 'database':
        return 'warning' as const;
      case 'tool':
        return 'info' as const;
      default:
        return 'default' as const;
    }
  };

  /**
   * Open version history dialog
   */
  const handleViewHistory = async (taxonomy: SkillTaxonomy) => {
    setSelectedTaxonomyForHistory(taxonomy);
    setHistoryDialogOpen(true);
    setLoadingVersions(true);
    setVersions([]);

    try {
      const response = await fetch(`http://localhost:8000/api/taxonomy-versions/${taxonomy.id}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch versions: ${response.statusText}`);
      }

      const result: TaxonomyVersionListResponse = await response.json();
      setVersions(result.versions || []);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : t('industryTaxonomy.errors.failedToLoadVersions');
      setError(errorMessage);
    } finally {
      setLoadingVersions(false);
    }
  };

  /**
   * Handle rollback to a specific version
   */
  const handleRollback = async (versionId: string) => {
    if (!selectedTaxonomyForHistory) return;

    setRollingBack(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/taxonomy-versions/${selectedTaxonomyForHistory.id}/rollback/${versionId}`,
        {
          method: 'POST',
        }
      );

      if (!response.ok) {
        throw new Error(`${t('industryTaxonomy.errors.failedToRollback')}: ${response.statusText}`);
      }

      // Refresh the taxonomy list and version history
      await fetchTaxonomies();
      await handleViewHistory(selectedTaxonomyForHistory);

      setHistoryDialogOpen(false);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : t('industryTaxonomy.errors.failedToRollback');
      setError(errorMessage);
    } finally {
      setRollingBack(false);
    }
  };

  /**
   * Handle publish/unpublish toggle click
   */
  const handlePublishClick = (taxonomy: SkillTaxonomy) => {
    setTaxonomyToPublish(taxonomy);
    setPublishingDialogOpen(true);
  };

  /**
   * Confirm publish/unpublish toggle
   */
  const handlePublishConfirm = async () => {
    if (!taxonomyToPublish) return;

    setTogglingPublic(true);
    try {
      const response = await fetch(`${apiUrl}/${taxonomyToPublish.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          is_public: !taxonomyToPublish.is_public,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to update taxonomy: ${response.statusText}`);
      }

      const updated: SkillTaxonomy = await response.json();
      setTaxonomies(taxonomies.map((t) => (t.id === updated.id ? updated : t)));
      setPublishingDialogOpen(false);
      setTaxonomyToPublish(null);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to update taxonomy';
      setError(errorMessage);
    } finally {
      setTogglingPublic(false);
    }
  };

  /**
   * Export taxonomies as JSON
   */
  const exportAsJSON = useCallback(() => {
    const exportData = {
      industry: selectedIndustry,
      exported_at: new Date().toISOString(),
      total_count: taxonomies.length,
      skills: taxonomies.map((t) => ({
        skill_name: t.skill_name,
        variants: t.variants,
        context: t.context,
        is_active: t.is_active,
      })),
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `skill-taxonomies-${selectedIndustry}-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    setExportMenuAnchor(null);
  }, [selectedIndustry, taxonomies]);

  /**
   * Export taxonomies as CSV
   */
  const exportAsCSV = useCallback(() => {
    const headers = ['Skill Name', 'Variants', 'Context', 'Active'];
    const rows = taxonomies.map((t) => [
      t.skill_name,
      `"${t.variants.join(', ')}"`,
      t.context || '',
      t.is_active ? 'Yes' : 'No',
    ]);

    const csvContent = [headers.join(','), ...rows.map((row) => row.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `skill-taxonomies-${selectedIndustry}-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    setExportMenuAnchor(null);
  }, [selectedIndustry, taxonomies]);

  /**
   * Validate import file
   */
  const validateImportFile = useCallback((file: File): string | null => {
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!['.json', '.csv'].includes(fileExtension)) {
      return 'Invalid file type. Please upload a JSON or CSV file.';
    }
    return null;
  }, []);

  /**
   * Handle import file selection
   */
  const handleImportFileSelect = useCallback(
    (file: File) => {
      setImportFile(null);
      setImportError(null);
      setImportSuccess(false);
      setImportProgress(0);

      const validationError = validateImportFile(file);
      if (validationError) {
        setImportError(validationError);
        return;
      }

      setImportFile(file);
      importTaxonomies(file);
    },
    [validateImportFile]
  );

  /**
   * Import taxonomies from file
   */
  const importTaxonomies = useCallback(
    async (file: File) => {
      setImporting(true);
      setImportProgress(0);

      try {
        const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
        let skillsToImport: SkillTaxonomyEntry[] = [];

        if (fileExtension === '.json') {
          const text = await file.text();
          const data = JSON.parse(text);

          if (data.skills && Array.isArray(data.skills)) {
            skillsToImport = data.skills.map((s: any) => ({
              skill_name: s.skill_name,
              variants: Array.isArray(s.variants) ? s.variants : [],
              context: s.context,
              is_active: s.is_active !== undefined ? s.is_active : true,
            }));
          } else if (Array.isArray(data)) {
            skillsToImport = data.map((s: any) => ({
              skill_name: s.skill_name,
              variants: Array.isArray(s.variants) ? s.variants : [],
              context: s.context,
              is_active: s.is_active !== undefined ? s.is_active : true,
            }));
          }
        } else if (fileExtension === '.csv') {
          const text = await file.text();
          const lines = text.split('\n').slice(1);
          skillsToImport = lines
            .filter((line) => line.trim())
            .map((line) => {
              const parts = line.match(/(".*?"|[^",\s]+)(?=\s*,|\s*$)/g) || [];
              const variants = parts[1]?.replace(/"/g, '').split(',').map((v) => v.trim()) || [];
              return {
                skill_name: parts[0]?.replace(/"/g, '') || '',
                variants,
                context: parts[2]?.replace(/"/g, '') || undefined,
                is_active: parts[3]?.replace(/"/g, '').toLowerCase() === 'yes',
              };
            })
            .filter((s) => s.skill_name);
        }

        setImportProgress(50);

        if (skillsToImport.length === 0) {
          throw new Error('No valid skills found in file');
        }

        const response = await fetch(apiUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            industry: selectedIndustry,
            skills: skillsToImport,
          }),
        });

        if (!response.ok) {
          throw new Error(`Failed to import taxonomies: ${response.statusText}`);
        }

        const result: SkillTaxonomyListResponse = await response.json();
        setImportProgress(100);

        if (result.skills && result.skills.length > 0) {
          setTaxonomies([...taxonomies, ...result.skills]);
          setImportSuccess(true);
          setTimeout(() => {
            setImportDialogOpen(false);
            setImportFile(null);
            setImportSuccess(false);
          }, 2000);
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to import taxonomies';
        setImportError(errorMessage);
      } finally {
        setImporting(false);
      }
    },
    [selectedIndustry, taxonomies, apiUrl]
  );

  /**
   * Handle file input change for import
   */
  const handleImportInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0 && files[0]) {
        handleImportFileSelect(files[0]);
      }
    },
    [handleImportFileSelect]
  );

  /**
   * Reset import state
   */
  const handleImportReset = useCallback(() => {
    setImportFile(null);
    setImportError(null);
    setImportSuccess(false);
    setImportProgress(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  /**
   * Render loading state
   */
  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          py: 8,
        }}
      >
        <CircularProgress size={60} sx={{ mb: 3 }} />
        <Typography variant="h6" color="text.secondary">
          {t('industryTaxonomy.loading')}
        </Typography>
      </Box>
    );
  }

  /**
   * Render error state
   */
  if (error) {
    return (
      <Alert
        severity="error"
        action={
          <Button color="inherit" onClick={fetchTaxonomies} startIcon={<RefreshIcon />}>
            {t('common.tryAgain')}
          </Button>
        }
      >
        <AlertTitle>{t('industryTaxonomy.errorTitle')}</AlertTitle>
        {error}
      </Alert>
    );
  }

  const activeCount = taxonomies.filter((t) => t.is_active).length;
  const inactiveCount = taxonomies.length - activeCount;

  return (
    <Stack spacing={3}>
      {/* Header Section with View Tabs */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5" fontWeight={600}>
            {t('industryTaxonomy.title')}
          </Typography>
        </Box>

        {/* View Tabs: Manage vs Browse */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
          <Tabs value={currentTab} onChange={(_e, newValue) => setCurrentTab(newValue)}>
            <Tab label="Manage Taxonomies" value="manage" />
            <Tab label="Browse Public" value="browse" />
          </Tabs>
        </Box>

        {currentTab === 'manage' && (
          <>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Stack direction="row" spacing={1}>
                <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchTaxonomies} size="small">
                  {t('industryTaxonomy.refreshButton')}
                </Button>
                {selectedIndustry === 'it' && (
                  <Button
                    variant="contained"
                    color="primary"
                    startIcon={<CloudUploadIcon />}
                    onClick={loadITTaxonomy}
                    size="small"
                  >
                    Load IT Taxonomy
                  </Button>
                )}
                <Button
                  variant="outlined"
                  startIcon={<UploadIcon />}
                  onClick={() => setImportDialogOpen(true)}
                  size="small"
                >
                  Import
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<DownloadIcon />}
                  onClick={(e) => setExportMenuAnchor(e.currentTarget)}
                  size="small"
                >
                  Export
                </Button>
              </Stack>
            </Box>

            {/* Export Menu */}
            <Menu
              anchorEl={exportMenuAnchor}
              open={Boolean(exportMenuAnchor)}
              onClose={() => setExportMenuAnchor(null)}
            >
              <MenuItem onClick={exportAsJSON} disabled={taxonomies.length === 0}>
                <FileDownloadIcon sx={{ mr: 1 }} />
                Export as JSON
              </MenuItem>
              <MenuItem onClick={exportAsCSV} disabled={taxonomies.length === 0}>
                <FileDownloadIcon sx={{ mr: 1 }} />
                Export as CSV
              </MenuItem>
            </Menu>

            {/* Industry Selector Tabs */}
            <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
              <Tabs
                value={selectedIndustry}
                onChange={handleIndustryChange}
                variant="scrollable"
                scrollButtons="auto"
              >
                {industries.map((industry) => (
                  <Tab
                    key={industry}
                    label={t(`industryTaxonomy.industries.${industry}`)}
                    value={industry}
                  />
                ))}
              </Tabs>
            </Box>

            {/* Summary Statistics */}
            <Grid container spacing={2}>
          <Grid item xs={6} sm={4}>
            <Card variant="outlined" sx={{ borderColor: 'primary.main' }}>
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="primary.main" fontWeight={700}>
                  {taxonomies.length}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {t('industryTaxonomy.totalSkills')}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={4}>
            <Card variant="outlined" sx={{ borderColor: 'success.main' }}>
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="success.main" fontWeight={700}>
                  {activeCount}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {t('industryTaxonomy.active')}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card variant="outlined" sx={{ borderColor: inactiveCount > 0 ? 'warning.main' : 'text.disabled' }}>
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color={inactiveCount > 0 ? 'warning.main' : 'text.disabled'} fontWeight={700}>
                  {inactiveCount}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {t('industryTaxonomy.inactive')}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

            {/* Create Button */}
            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={handleCreate}
                size="large"
              >
                {t('industryTaxonomy.addButton')}
              </Button>
            </Box>
          </>
        )}

        {/* Browse tab content */}
        {currentTab === 'browse' && (
          <PublicTaxonomyBrowser organizationId={organizationId} />
        )}
      </Paper>

      {/* Taxonomies List - Only show in manage tab */}
      {currentTab === 'manage' && (
        <>
          {taxonomies.length === 0 ? (
            <Paper elevation={1} sx={{ p: 4, textAlign: 'center' }}>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                {t('industryTaxonomy.noSkills')}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t('industryTaxonomy.noSkillsMessage')}
              </Typography>
            </Paper>
          ) : (
        <Grid container spacing={2}>
          {taxonomies.map((taxonomy) => (
            <Grid item xs={12} md={6} key={taxonomy.id}>
              <Card
                variant="outlined"
                sx={{
                  opacity: taxonomy.is_active ? 1 : 0.6,
                  transition: 'opacity 0.2s',
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Typography variant="h6" fontWeight={600}>
                      {taxonomy.skill_name}
                    </Typography>
                    <Stack direction="row" spacing={1}>
                      <IconButton
                        size="small"
                        onClick={() => handlePublishClick(taxonomy)}
                        color={taxonomy.is_public ? 'success' : 'default'}
                        title={taxonomy.is_public ? 'Unpublish' : 'Publish as public'}
                      >
                        <PublicIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleViewHistory(taxonomy)}
                        color="info"
                      >
                        <HistoryIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleEdit(taxonomy)}
                        color="primary"
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDeleteClick(taxonomy)}
                        color="error"
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Stack>
                  </Box>

                  {taxonomy.context && (
                    <Box sx={{ mb: 2 }}>
                      <Chip
                        label={taxonomy.context}
                        size="small"
                        color={getContextColor(taxonomy.context)}
                        variant="outlined"
                      />
                      <Chip
                        label={taxonomy.is_active ? t('industryTaxonomy.active') : t('industryTaxonomy.inactive')}
                        size="small"
                        color={taxonomy.is_active ? 'success' : 'default'}
                        variant="filled"
                        sx={{ ml: 1 }}
                      />
                      {taxonomy.is_public && (
                        <Chip
                          icon={<PublicIcon fontSize="small" />}
                          label="Public"
                          size="small"
                          color="info"
                          variant="filled"
                          sx={{ ml: 1 }}
                        />
                      )}
                    </Box>
                  )}
                  {!taxonomy.context && (
                    <Box sx={{ mb: 2 }}>
                      <Chip
                        label={taxonomy.is_active ? t('industryTaxonomy.active') : t('industryTaxonomy.inactive')}
                        size="small"
                        color={taxonomy.is_active ? 'success' : 'default'}
                        variant="filled"
                      />
                      {taxonomy.is_public && (
                        <Chip
                          icon={<PublicIcon fontSize="small" />}
                          label="Public"
                          size="small"
                          color="info"
                          variant="filled"
                          sx={{ ml: 1 }}
                        />
                      )}
                    </Box>
                  )}

                  <Divider sx={{ my: 1 }} />

                  <Box sx={{ mt: 2 }}>
                    <Typography variant="caption" color="text.secondary" gutterBottom display="block">
                      {t('industryTaxonomy.skill.variants')}
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {taxonomy.variants.map((variant, index) => (
                        <Chip
                          key={index}
                          label={variant}
                          size="small"
                          variant="filled"
                          color="primary"
                        />
                      ))}
                    </Box>
                  </Box>

                  <Box sx={{ mt: 2 }}>
                    <Typography variant="caption" color="text.secondary" gutterBottom display="block">
                      {t('industryTaxonomy.skill.usage')}
                    </Typography>
                    <Stack direction="row" spacing={2}>
                      <Typography variant="caption" color="text.secondary">
                        {t('industryTaxonomy.skill.viewCount')}: {taxonomy.view_count}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {t('industryTaxonomy.skill.useCount')}: {taxonomy.use_count}
                      </Typography>
                    </Stack>
                  </Box>

                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
                    {t('industryTaxonomy.skill.createdAt')}: {new Date(taxonomy.created_at).toLocaleDateString()}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
            </Grid>
          )}
        </>
      )}

      {/* Create/Edit Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={() => !submitting && setDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">
              {editingTaxonomy ? t('industryTaxonomy.dialog.editTitle') : t('industryTaxonomy.dialog.addTitle')}
            </Typography>
            <IconButton
              onClick={() => setDialogOpen(false)}
              disabled={submitting}
              size="small"
            >
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            <TextField
              label={t('industryTaxonomy.dialog.skillName')}
              fullWidth
              required
              value={formData.skill_name}
              onChange={(e) => setFormData({ ...formData, skill_name: e.target.value })}
              placeholder={t('industryTaxonomy.dialog.skillNamePlaceholder')}
              disabled={submitting}
            />

            <TextField
              label={t('industryTaxonomy.dialog.variants')}
              fullWidth
              required
              multiline
              rows={3}
              value={formData.variants}
              onChange={(e) => setFormData({ ...formData, variants: e.target.value })}
              placeholder={t('industryTaxonomy.dialog.variantsPlaceholder')}
              disabled={submitting}
              helperText={t('industryTaxonomy.dialog.variantsHelper')}
            />

            <TextField
              label={t('industryTaxonomy.dialog.context')}
              fullWidth
              select
              value={formData.context}
              onChange={(e) => setFormData({ ...formData, context: e.target.value })}
              disabled={submitting}
            >
              <MenuItem value="">{t('industryTaxonomy.dialog.contextNone')}</MenuItem>
              <MenuItem value="web_framework">{t('industryTaxonomy.dialog.contextWebFramework')}</MenuItem>
              <MenuItem value="language">{t('industryTaxonomy.dialog.contextLanguage')}</MenuItem>
              <MenuItem value="database">{t('industryTaxonomy.dialog.contextDatabase')}</MenuItem>
              <MenuItem value="tool">{t('industryTaxonomy.dialog.contextTool')}</MenuItem>
              <MenuItem value="library">{t('industryTaxonomy.dialog.contextLibrary')}</MenuItem>
            </TextField>

            <FormControl fullWidth>
              <InputLabel>{t('industryTaxonomy.dialog.status')}</InputLabel>
              <Select
                value={formData.is_active.toString()}
                label={t('industryTaxonomy.dialog.status')}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.value === 'true' })}
                disabled={submitting}
              >
                <MenuItem value="true">{t('industryTaxonomy.dialog.statusActive')}</MenuItem>
                <MenuItem value="false">{t('industryTaxonomy.dialog.statusInactive')}</MenuItem>
              </Select>
            </FormControl>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)} disabled={submitting}>
            {t('industryTaxonomy.dialog.cancel')}
          </Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={submitting || !formData.skill_name || !formData.variants}
            startIcon={submitting ? <CircularProgress size={16} /> : null}
          >
            {submitting ? t('industryTaxonomy.dialog.saving') : editingTaxonomy ? t('industryTaxonomy.dialog.update') : t('industryTaxonomy.dialog.create')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>{t('industryTaxonomy.deleteDialog.title')}</DialogTitle>
        <DialogContent>
          <Typography variant="body1">
            {t('industryTaxonomy.deleteDialog.message', {
              skill: taxonomyToDelete?.skill_name
            })}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {t('industryTaxonomy.deleteDialog.warning')}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)} disabled={submitting}>
            {t('industryTaxonomy.deleteDialog.cancel')}
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            variant="contained"
            color="error"
            disabled={submitting}
            startIcon={submitting ? <CircularProgress size={16} /> : <DeleteIcon />}
          >
            {submitting ? t('industryTaxonomy.deleteDialog.deleting') : t('industryTaxonomy.deleteDialog.confirm')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Version History Dialog */}
      <Dialog
        open={historyDialogOpen}
        onClose={() => !loadingVersions && !rollingBack && setHistoryDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">
              {t('industryTaxonomy.historyDialog.title', { skill: selectedTaxonomyForHistory?.skill_name })}
            </Typography>
            <IconButton
              onClick={() => setHistoryDialogOpen(false)}
              disabled={loadingVersions || rollingBack}
              size="small"
            >
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          {loadingVersions ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : versions.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography variant="body2" color="text.secondary">
                {t('industryTaxonomy.historyDialog.noVersions')}
              </Typography>
            </Box>
          ) : (
            <Stack spacing={2} sx={{ mt: 1 }}>
              {versions.map((version) => (
                <Card
                  key={version.id}
                  variant="outlined"
                  sx={{
                    borderColor: version.is_latest ? 'primary.main' : 'divider',
                    backgroundColor: version.is_latest ? 'action.hover' : 'background.paper',
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Box>
                        <Typography variant="subtitle1" fontWeight={600}>
                          {t('industryTaxonomy.historyDialog.version')} {version.version}
                          {version.is_latest && (
                            <Chip
                              label={t('industryTaxonomy.historyDialog.current')}
                              size="small"
                              color="primary"
                              sx={{ ml: 1 }}
                            />
                          )}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {new Date(version.created_at).toLocaleString()}
                        </Typography>
                      </Box>
                      {!version.is_latest && (
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={() => handleRollback(version.id)}
                          disabled={rollingBack}
                          startIcon={rollingBack ? <CircularProgress size={14} /> : <HistoryIcon />}
                        >
                          {t('industryTaxonomy.historyDialog.rollback')}
                        </Button>
                      )}
                    </Box>

                    <Divider sx={{ my: 1 }} />

                    <Box sx={{ mt: 2 }}>
                      <Typography variant="caption" color="text.secondary" gutterBottom display="block">
                        {t('industryTaxonomy.skill.variants')}
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {version.variants.map((variant, index) => (
                          <Chip
                            key={index}
                            label={variant}
                            size="small"
                            variant="filled"
                            color={version.is_latest ? 'primary' : 'default'}
                          />
                        ))}
                      </Box>
                    </Box>

                    {version.context && (
                      <Box sx={{ mt: 2 }}>
                        <Chip
                          label={version.context}
                          size="small"
                          color={getContextColor(version.context)}
                          variant="outlined"
                        />
                        <Chip
                          label={version.is_active ? t('industryTaxonomy.active') : t('industryTaxonomy.inactive')}
                          size="small"
                          color={version.is_active ? 'success' : 'default'}
                          variant="filled"
                          sx={{ ml: 1 }}
                        />
                      </Box>
                    )}
                  </CardContent>
                </Card>
              ))}
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setHistoryDialogOpen(false)} disabled={loadingVersions || rollingBack}>
            {t('industryTaxonomy.historyDialog.close')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Publish/Unpublish Confirmation Dialog */}
      <Dialog open={publishingDialogOpen} onClose={() => !togglingPublic && setPublishingDialogOpen(false)}>
        <DialogTitle>
          {taxonomyToPublish?.is_public ? 'Unpublish Taxonomy' : 'Publish Taxonomy'}
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1">
            {taxonomyToPublish?.is_public
              ? `Make "${taxonomyToPublish?.skill_name}" private?`
              : `Publish "${taxonomyToPublish?.skill_name}" as public?`}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {taxonomyToPublish?.is_public
              ? 'This will remove the taxonomy from the public gallery. Other organizations will no longer be able to fork it.'
              : 'This will make the taxonomy visible in the public gallery. Other organizations will be able to fork it to their own collections.'}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPublishingDialogOpen(false)} disabled={togglingPublic}>
            Cancel
          </Button>
          <Button
            onClick={handlePublishConfirm}
            variant="contained"
            color={taxonomyToPublish?.is_public ? 'warning' : 'primary'}
            disabled={togglingPublic}
            startIcon={togglingPublic ? <CircularProgress size={16} /> : (taxonomyToPublish?.is_public ? null : <CloudUploadIcon />)}
          >
            {togglingPublic ? 'Updating...' : taxonomyToPublish?.is_public ? 'Unpublish' : 'Publish'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Import Dialog */}
      <Dialog
        open={importDialogOpen}
        onClose={() => !importing && setImportDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">Import Taxonomies</Typography>
            <IconButton
              onClick={() => setImportDialogOpen(false)}
              disabled={importing}
              size="small"
            >
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            {/* Hidden file input */}
            <input
              ref={fileInputRef}
              type="file"
              accept=".json,.csv"
              onChange={handleImportInputChange}
              style={{ display: 'none' }}
              disabled={importing}
            />

            {/* Error Alert */}
            {importError && (
              <Alert
                severity="error"
                action={
                  !importing && (
                    <Button
                      color="inherit"
                      size="small"
                      onClick={handleImportReset}
                      disabled={importing}
                    >
                      Try Again
                    </Button>
                  )
                }
              >
                {importError}
              </Alert>
            )}

            {/* Success Alert */}
            {importSuccess && (
              <Alert
                severity="success"
                action={
                  <Button
                    color="inherit"
                    size="small"
                    onClick={() => setImportDialogOpen(false)}
                    disabled={importing}
                  >
                    Close
                  </Button>
                }
              >
                Taxonomies imported successfully!
              </Alert>
            )}

            {/* Upload Area */}
            {!importSuccess && (
              <Paper
                elevation={1}
                onClick={() => !importing && fileInputRef.current?.click()}
                sx={{
                  p: 4,
                  border: '2px dashed',
                  borderColor: importError ? 'error.main' : 'divider',
                  bgcolor: 'background.paper',
                  transition: 'all 0.2s ease-in-out',
                  cursor: importing ? 'wait' : 'pointer',
                  textAlign: 'center',
                }}
              >
                <CloudUploadIcon
                  sx={{
                    fontSize: 48,
                    color: 'action.disabled',
                    mb: 2,
                  }}
                />
                <Typography variant="h6" gutterBottom fontWeight={600}>
                  {importing ? 'Importing...' : 'Choose a file to import'}
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  {importing ? 'Please wait while we import the taxonomies' : 'Click to browse or drag and drop'}
                </Typography>
                <Stack direction="row" spacing={1} justifyContent="center" mb={2}>
                  <Chip label="JSON" size="small" variant="outlined" />
                  <Chip label="CSV" size="small" variant="outlined" />
                </Stack>
                {!importing && (
                  <Button
                    variant="contained"
                    startIcon={<UploadIcon />}
                    onClick={(e) => {
                      e.stopPropagation();
                      fileInputRef.current?.click();
                    }}
                  >
                    Choose File
                  </Button>
                )}
              </Paper>
            )}

            {/* Selected File Info */}
            {importFile && !importSuccess && (
              <Box sx={{ mt: 2 }}>
                <Stack
                  direction="row"
                  spacing={2}
                  alignItems="center"
                  justifyContent="center"
                >
                  <Typography variant="body2" color="text.primary">
                    <strong>{importFile.name}</strong>
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    ({(importFile.size / 1024).toFixed(1)} KB)
                  </Typography>
                  {!importing && (
                    <Button
                      size="small"
                      startIcon={<DeleteIcon />}
                      onClick={handleImportReset}
                      color="error"
                    >
                      Remove
                    </Button>
                  )}
                </Stack>
              </Box>
            )}

            {/* Progress Bar */}
            {importing && (
              <Box sx={{ mt: 2 }}>
                <LinearProgress
                  variant="determinate"
                  value={importProgress}
                  sx={{ height: 8, borderRadius: 4 }}
                />
                <Typography
                  variant="body2"
                  align="center"
                  color="text.secondary"
                  sx={{ mt: 1 }}
                >
                  {importProgress}%
                </Typography>
              </Box>
            )}

            {/* Help Text */}
            {!importSuccess && (
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                Import taxonomies from a JSON or CSV file. The file will be added to the current industry: {selectedIndustry}
              </Typography>
            )}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setImportDialogOpen(false)} disabled={importing}>
            {importSuccess ? 'Close' : 'Cancel'}
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
};

export default IndustryTaxonomyManager;
