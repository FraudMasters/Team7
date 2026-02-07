import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { config } from '@/config';
import {
  Box,
  Paper,
  Typography,
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
  Slider,
  Chip,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Close as CloseIcon,
  Save as SaveIcon,
} from '@mui/icons-material';

/**
 * Weight profile entry interface
 */
interface WeightProfile {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  keyword_weight: number;
  tfidf_weight: number;
  vector_weight: number;
  is_default: boolean;
  is_preset: boolean;
  preset_type?: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

/**
 * List response from backend
 */
interface WeightProfileListResponse {
  organization_id?: string;
  profiles: WeightProfile[];
  total_count: number;
}

/**
 * Form data for creating/editing weight profiles
 */
interface WeightProfileFormData {
  name: string;
  description: string;
  keyword_weight: number;
  tfidf_weight: number;
  vector_weight: number;
  is_default: boolean;
}

/**
 * Preset profile definitions
 */
interface PresetProfile {
  name: string;
  description: string;
  keyword_weight: number;
  tfidf_weight: number;
  vector_weight: number;
  preset_type: string;
}

/**
 * MatchingWeightsEditor Component Props
 */
interface MatchingWeightsEditorProps {
  /** Organization ID to manage weight profiles for */
  organizationId: string;
  /** API endpoint URL for matching weights */
  apiUrl?: string;
  /** Callback when profile is saved */
  onProfileSave?: (profile: WeightProfile) => void;
}

/**
 * Preset profiles
 */
const PRESET_PROFILES: PresetProfile[] = [
  {
    name: 'Technical',
    description: 'Emphasizes exact keyword matching for technical roles with specific skill requirements',
    keyword_weight: 0.6,
    tfidf_weight: 0.3,
    vector_weight: 0.1,
    preset_type: 'technical',
  },
  {
    name: 'Creative',
    description: 'Prioritizes semantic understanding for creative and conceptual roles',
    keyword_weight: 0.2,
    tfidf_weight: 0.2,
    vector_weight: 0.6,
    preset_type: 'creative',
  },
  {
    name: 'Executive',
    description: 'Balanced approach for executive and leadership positions',
    keyword_weight: 0.33,
    tfidf_weight: 0.34,
    vector_weight: 0.33,
    preset_type: 'executive',
  },
  {
    name: 'Balanced',
    description: 'Equal weighting for all matching algorithms',
    keyword_weight: 0.33,
    tfidf_weight: 0.33,
    vector_weight: 0.34,
    preset_type: 'balanced',
  },
];

/**
 * MatchingWeightsEditor Component
 *
 * Provides a comprehensive admin interface for managing matching algorithm
 * weight profiles. Features include:
 * - List all weight profiles for the organization
 * - Create custom weight profiles with sliders
 * - Edit existing profiles
 * - Delete custom profiles
 * - Preset profiles for common use cases
 * - Auto-normalization to ensure weights sum to 100%
 * - Set default profile for organization
 *
 * @example
 * ```tsx
 * <MatchingWeightsEditor organizationId="org123" />
 * ```
 */
const MatchingWeightsEditor: React.FC<MatchingWeightsEditorProps> = ({
  organizationId,
  apiUrl = `${config.api.url}/api/matching-weights`,
  onProfileSave,
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [profiles, setProfiles] = useState<WeightProfile[]>([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingProfile, setEditingProfile] = useState<WeightProfile | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [profileToDelete, setProfileToDelete] = useState<WeightProfile | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Form state
  const [formData, setFormData] = useState<WeightProfileFormData>({
    name: '',
    description: '',
    keyword_weight: 0.33,
    tfidf_weight: 0.33,
    vector_weight: 0.34,
    is_default: false,
  });

  /**
   * Fetch weight profiles from backend
   */
  const fetchProfiles = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiUrl}/?organization_id=${organizationId}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch profiles: ${response.statusText}`);
      }

      const result: WeightProfileListResponse = await response.json();
      setProfiles(result.profiles || []);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load weight profiles';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (organizationId) {
      fetchProfiles();
    }
  }, [organizationId]);

  /**
   * Normalize weights to sum to 1.0
   */
  const normalizeWeights = (keyword: number, tfidf: number, vector: number) => {
    const total = keyword + tfidf + vector;
    if (total === 0) {
      return { keyword_weight: 0.33, tfidf_weight: 0.33, vector_weight: 0.34 };
    }
    return {
      keyword_weight: Math.round((keyword / total) * 100) / 100,
      tfidf_weight: Math.round((tfidf / total) * 100) / 100,
      vector_weight: Math.round((vector / total) * 100) / 100,
    };
  };

  /**
   * Open create dialog
   */
  const handleCreate = () => {
    setEditingProfile(null);
    setFormData({
      name: '',
      description: '',
      keyword_weight: 0.33,
      tfidf_weight: 0.33,
      vector_weight: 0.34,
      is_default: false,
    });
    setDialogOpen(true);
  };

  /**
   * Open edit dialog
   */
  const handleEdit = (profile: WeightProfile) => {
    setEditingProfile(profile);
    setFormData({
      name: profile.name,
      description: profile.description || '',
      keyword_weight: profile.keyword_weight,
      tfidf_weight: profile.tfidf_weight,
      vector_weight: profile.vector_weight,
      is_default: profile.is_default,
    });
    setDialogOpen(true);
  };

  /**
   * Open delete confirmation dialog
   */
  const handleDeleteClick = (profile: WeightProfile) => {
    setProfileToDelete(profile);
    setDeleteDialogOpen(true);
  };

  /**
   * Confirm delete
   */
  const handleDeleteConfirm = async () => {
    if (!profileToDelete) return;

    setSubmitting(true);
    try {
      const response = await fetch(`${apiUrl}/${profileToDelete.id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`Failed to delete profile: ${response.statusText}`);
      }

      // Optimistic update
      setProfiles(profiles.filter((p) => p.id !== profileToDelete.id));
      setDeleteDialogOpen(false);
      setProfileToDelete(null);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to delete profile';
      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  /**
   * Apply preset profile to form
   */
  const handleApplyPreset = (preset: PresetProfile) => {
    setFormData({
      ...formData,
      keyword_weight: preset.keyword_weight,
      tfidf_weight: preset.tfidf_weight,
      vector_weight: preset.vector_weight,
      description: preset.description,
    });
  };

  /**
   * Handle slider change with auto-normalization
   */
  const handleSliderChange = (field: 'keyword_weight' | 'tfidf_weight' | 'vector_weight', value: number) => {
    const newFormData = { ...formData, [field]: value };
    const normalized = normalizeWeights(
      newFormData.keyword_weight,
      newFormData.tfidf_weight,
      newFormData.vector_weight
    );
    setFormData({ ...newFormData, ...normalized });
  };

  /**
   * Submit form (create or update)
   */
  const handleSubmit = async () => {
    setSubmitting(true);
    setError(null);

    try {
      // Normalize weights before submission
      const normalized = normalizeWeights(
        formData.keyword_weight,
        formData.tfidf_weight,
        formData.vector_weight
      );

      const submitData = {
        ...formData,
        ...normalized,
      };

      if (editingProfile) {
        // Update existing profile
        const response = await fetch(`${apiUrl}/${editingProfile.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(submitData),
        });

        if (!response.ok) {
          throw new Error(`Failed to update profile: ${response.statusText}`);
        }

        const updated: WeightProfile = await response.json();
        setProfiles(profiles.map((p) => (p.id === updated.id ? updated : p)));

        if (onProfileSave) {
          onProfileSave(updated);
        }
      } else {
        // Create new profile
        const response = await fetch(apiUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            organization_id: organizationId,
            ...submitData,
          }),
        });

        if (!response.ok) {
          throw new Error(`Failed to create profile: ${response.statusText}`);
        }

        const created: WeightProfile = await response.json();
        setProfiles([...profiles, created]);

        if (onProfileSave) {
          onProfileSave(created);
        }
      }

      setDialogOpen(false);
      setFormData({
        name: '',
        description: '',
        keyword_weight: 0.33,
        tfidf_weight: 0.33,
        vector_weight: 0.34,
        is_default: false,
      });
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to save profile';
      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  /**
   * Get preset type color
   */
  const getPresetColor = (presetType?: string) => {
    switch (presetType) {
      case 'technical':
        return 'primary' as const;
      case 'creative':
        return 'secondary' as const;
      case 'executive':
        return 'warning' as const;
      case 'balanced':
        return 'info' as const;
      default:
        return 'default' as const;
    }
  };

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
          Loading weight profiles...
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
          <Button color="inherit" onClick={fetchProfiles} startIcon={<RefreshIcon />}>
            Try Again
          </Button>
        }
      >
        <AlertTitle>Error</AlertTitle>
        {error}
      </Alert>
    );
  }

  const customProfiles = profiles.filter((p) => !p.is_preset);
  const presetProfiles = profiles.filter((p) => p.is_preset);
  const defaultProfile = profiles.find((p) => p.is_default);

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5" fontWeight={600}>
            Matching Algorithm Weights
          </Typography>
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchProfiles} size="small">
            Refresh
          </Button>
        </Box>

        {/* Summary Statistics */}
        <Grid container spacing={2}>
          <Grid item xs={6} sm={4}>
            <Card variant="outlined" sx={{ borderColor: 'primary.main' }}>
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="primary.main" fontWeight={700}>
                  {profiles.length}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Total Profiles
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={4}>
            <Card variant="outlined" sx={{ borderColor: 'success.main' }}>
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="success.main" fontWeight={700}>
                  {presetProfiles.length}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Presets
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card variant="outlined" sx={{ borderColor: 'info.main' }}>
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="info.main" fontWeight={700}>
                  {customProfiles.length}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Custom
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
            Create Custom Profile
          </Button>
        </Box>
      </Paper>

      {/* Preset Profiles */}
      {presetProfiles.length > 0 && (
        <Paper elevation={1} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Preset Profiles
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Pre-configured profiles for common use cases
          </Typography>
          <Grid container spacing={2}>
            {presetProfiles.map((profile) => (
              <Grid item xs={12} md={6} key={profile.id}>
                <Card
                  variant="outlined"
                  sx={{
                    opacity: defaultProfile?.id === profile.id ? 1 : 0.7,
                    border: defaultProfile?.id === profile.id ? 2 : 1,
                    borderColor: defaultProfile?.id === profile.id ? 'primary.main' : 'divider',
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Typography variant="h6" fontWeight={600}>
                        {profile.name}
                      </Typography>
                      <Stack direction="row" spacing={1}>
                        {profile.preset_type && (
                          <Chip
                            label={profile.preset_type}
                            size="small"
                            color={getPresetColor(profile.preset_type)}
                            variant="filled"
                          />
                        )}
                        {defaultProfile?.id === profile.id && (
                          <Chip
                            label="Default"
                            size="small"
                            color="primary"
                            variant="outlined"
                          />
                        )}
                      </Stack>
                    </Box>

                    {profile.description && (
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {profile.description}
                      </Typography>
                    )}

                    <Divider sx={{ my: 1 }} />

                    <Box sx={{ mt: 2 }}>
                      <Typography variant="caption" color="text.secondary" gutterBottom display="block">
                        Algorithm Weights
                      </Typography>
                      <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 0.5 }}>
                        <Chip
                          label={`Keyword: ${Math.round(profile.keyword_weight * 100)}%`}
                          size="small"
                          variant="outlined"
                        />
                        <Chip
                          label={`TF-IDF: ${Math.round(profile.tfidf_weight * 100)}%`}
                          size="small"
                          variant="outlined"
                        />
                        <Chip
                          label={`Vector: ${Math.round(profile.vector_weight * 100)}%`}
                          size="small"
                          variant="outlined"
                        />
                      </Stack>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      {/* Custom Profiles */}
      {customProfiles.length === 0 ? (
        <Paper elevation={1} sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No Custom Profiles
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Create custom weight profiles tailored to your specific hiring needs
          </Typography>
        </Paper>
      ) : (
        <Paper elevation={1} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Custom Profiles
          </Typography>
          <Grid container spacing={2}>
            {customProfiles.map((profile) => (
              <Grid item xs={12} md={6} key={profile.id}>
                <Card
                  variant="outlined"
                  sx={{
                    border: defaultProfile?.id === profile.id ? 2 : 1,
                    borderColor: defaultProfile?.id === profile.id ? 'primary.main' : 'divider',
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Typography variant="h6" fontWeight={600}>
                        {profile.name}
                      </Typography>
                      <Stack direction="row" spacing={1}>
                        <IconButton
                          size="small"
                          onClick={() => handleEdit(profile)}
                          color="primary"
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => handleDeleteClick(profile)}
                          color="error"
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Stack>
                    </Box>

                    {profile.description && (
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {profile.description}
                      </Typography>
                    )}

                    <Divider sx={{ my: 1 }} />

                    <Box sx={{ mt: 2 }}>
                      <Typography variant="caption" color="text.secondary" gutterBottom display="block">
                        Algorithm Weights
                      </Typography>
                      <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 0.5 }}>
                        <Chip
                          label={`Keyword: ${Math.round(profile.keyword_weight * 100)}%`}
                          size="small"
                          variant="filled"
                          color="primary"
                        />
                        <Chip
                          label={`TF-IDF: ${Math.round(profile.tfidf_weight * 100)}%`}
                          size="small"
                          variant="filled"
                          color="secondary"
                        />
                        <Chip
                          label={`Vector: ${Math.round(profile.vector_weight * 100)}%`}
                          size="small"
                          variant="filled"
                          color="info"
                        />
                      </Stack>
                    </Box>

                    {defaultProfile?.id === profile.id && (
                      <Chip
                        label="Default"
                        size="small"
                        color="primary"
                        variant="outlined"
                        sx={{ mt: 2 }}
                      />
                    )}
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      {/* Create/Edit Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={() => !submitting && setDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">
              {editingProfile ? 'Edit Weight Profile' : 'Create Weight Profile'}
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
            {/* Preset Profiles */}
            {!editingProfile && (
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Quick Start - Apply a Preset:
                </Typography>
                <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1 }}>
                  {PRESET_PROFILES.map((preset) => (
                    <Chip
                      key={preset.preset_type}
                      label={preset.name}
                      onClick={() => handleApplyPreset(preset)}
                      sx={{ cursor: 'pointer' }}
                      color={getPresetColor(preset.preset_type)}
                      variant="outlined"
                    />
                  ))}
                </Stack>
              </Box>
            )}

            <TextField
              label="Profile Name"
              fullWidth
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Technical Role Focus"
              disabled={submitting}
            />

            <TextField
              label="Description"
              fullWidth
              multiline
              rows={2}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Describe when to use this profile"
              disabled={submitting}
            />

            {/* Weight Sliders */}
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Algorithm Weights (auto-normalized to 100%)
              </Typography>

              <Stack spacing={3}>
                {/* Keyword Weight */}
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      Keyword Matching
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {Math.round(formData.keyword_weight * 100)}%
                    </Typography>
                  </Box>
                  <Slider
                    value={formData.keyword_weight * 100}
                    onChange={(_, value) => handleSliderChange('keyword_weight', (value as number) / 100)}
                    disabled={submitting}
                    valueLabelDisplay="auto"
                    valueLabelFormat={(value) => `${Math.round(value)}%`}
                    sx={{ color: 'primary.main' }}
                  />
                  <Typography variant="caption" color="text.secondary">
                    Exact keyword and phrase matching
                  </Typography>
                </Box>

                {/* TF-IDF Weight */}
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      TF-IDF Matching
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {Math.round(formData.tfidf_weight * 100)}%
                    </Typography>
                  </Box>
                  <Slider
                    value={formData.tfidf_weight * 100}
                    onChange={(_, value) => handleSliderChange('tfidf_weight', (value as number) / 100)}
                    disabled={submitting}
                    valueLabelDisplay="auto"
                    valueLabelFormat={(value) => `${Math.round(value)}%`}
                    sx={{ color: 'secondary.main' }}
                  />
                  <Typography variant="caption" color="text.secondary">
                    Term frequency-inverse document frequency
                  </Typography>
                </Box>

                {/* Vector Weight */}
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      Vector Similarity
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {Math.round(formData.vector_weight * 100)}%
                    </Typography>
                  </Box>
                  <Slider
                    value={formData.vector_weight * 100}
                    onChange={(_, value) => handleSliderChange('vector_weight', (value as number) / 100)}
                    disabled={submitting}
                    valueLabelDisplay="auto"
                    valueLabelFormat={(value) => `${Math.round(value)}%`}
                    sx={{ color: 'info.main' }}
                  />
                  <Typography variant="caption" color="text.secondary">
                    Semantic vector embeddings similarity
                  </Typography>
                </Box>
              </Stack>
            </Box>

            {/* Total Validation */}
            <Alert severity="info" variant="outlined">
              <Typography variant="body2">
                Weights are automatically normalized to sum to 100%:
                Keyword {Math.round(formData.keyword_weight * 100)}% +
                TF-IDF {Math.round(formData.tfidf_weight * 100)}% +
                Vector {Math.round(formData.vector_weight * 100)}% = {' '}
                {Math.round((formData.keyword_weight + formData.tfidf_weight + formData.vector_weight) * 100)}%
              </Typography>
            </Alert>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)} disabled={submitting}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={submitting || !formData.name}
            startIcon={submitting ? <CircularProgress size={16} /> : <SaveIcon />}
          >
            {submitting ? 'Saving...' : editingProfile ? 'Update Profile' : 'Create Profile'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Weight Profile</DialogTitle>
        <DialogContent>
          <Typography variant="body1">
            Are you sure you want to delete the weight profile "{profileToDelete?.name}"?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)} disabled={submitting}>
            Cancel
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            variant="contained"
            color="error"
            disabled={submitting}
            startIcon={submitting ? <CircularProgress size={16} /> : <DeleteIcon />}
          >
            {submitting ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
};

export default MatchingWeightsEditor;
