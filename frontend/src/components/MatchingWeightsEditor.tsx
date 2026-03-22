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
import RankingFeaturesEditor, {
  RankingFeatureWeights,
  DEFAULT_RANKING_WEIGHTS
} from './RankingFeaturesEditor';
import MatchingWeightsPreview from './MatchingWeightsPreview';

/**
 * Weight profile entry interface
 */
interface WeightProfile {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  skill_match_weight: number;
  experience_weight: number;
  education_weight: number;
  location_weight: number;
  keyword_weight: number;
  tfidf_weight: number;
  vector_weight: number;
  recency_weight: number;
  culture_fit_weight: number;
  salary_match_weight: number;
  availability_weight: number;
  certifications_weight: number;
  industry_experience_weight: number;
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
interface WeightProfileFormData extends RankingFeatureWeights {
  name: string;
  description: string;
  is_default: boolean;
}

/**
 * Preset profile definitions
 */
interface PresetProfile extends RankingFeatureWeights {
  name: string;
  description: string;
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
 * Preset profiles with all 13 ranking features
 */
const PRESET_PROFILES: PresetProfile[] = [
  {
    name: 'Technical',
    description: 'Emphasizes skills, certifications, and keyword matching for technical roles',
    skill_match_weight: 0.30,
    experience_weight: 0.15,
    education_weight: 0.08,
    location_weight: 0.03,
    keyword_weight: 0.15,
    tfidf_weight: 0.10,
    vector_weight: 0.05,
    recency_weight: 0.02,
    culture_fit_weight: 0.03,
    salary_match_weight: 0.03,
    availability_weight: 0.02,
    certifications_weight: 0.03,
    industry_experience_weight: 0.01,
    preset_type: 'technical',
  },
  {
    name: 'Creative',
    description: 'Prioritizes semantic understanding, culture fit, and portfolio for creative roles',
    skill_match_weight: 0.15,
    experience_weight: 0.10,
    education_weight: 0.12,
    location_weight: 0.04,
    keyword_weight: 0.05,
    tfidf_weight: 0.08,
    vector_weight: 0.25,
    recency_weight: 0.05,
    culture_fit_weight: 0.10,
    salary_match_weight: 0.02,
    availability_weight: 0.02,
    certifications_weight: 0.01,
    industry_experience_weight: 0.01,
    preset_type: 'creative',
  },
  {
    name: 'Executive',
    description: 'Balanced approach emphasizing experience, culture fit, and industry knowledge',
    skill_match_weight: 0.12,
    experience_weight: 0.20,
    education_weight: 0.10,
    location_weight: 0.05,
    keyword_weight: 0.08,
    tfidf_weight: 0.08,
    vector_weight: 0.10,
    recency_weight: 0.03,
    culture_fit_weight: 0.15,
    salary_match_weight: 0.03,
    availability_weight: 0.02,
    certifications_weight: 0.02,
    industry_experience_weight: 0.02,
    preset_type: 'executive',
  },
  {
    name: 'Balanced',
    description: 'Equal weighting across all ranking features',
    ...DEFAULT_RANKING_WEIGHTS,
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
  const [previewVacancyId, setPreviewVacancyId] = useState<string>('');
  const [baselineWeights, setBaselineWeights] = useState<RankingFeatureWeights>(DEFAULT_RANKING_WEIGHTS);

  // Form state
  const [formData, setFormData] = useState<WeightProfileFormData>({
    name: '',
    description: '',
    ...DEFAULT_RANKING_WEIGHTS,
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
   * Open create dialog
   */
  const handleCreate = () => {
    setEditingProfile(null);
    setFormData({
      name: '',
      description: '',
      ...DEFAULT_RANKING_WEIGHTS,
      is_default: false,
    });
    setBaselineWeights(DEFAULT_RANKING_WEIGHTS);
    setPreviewVacancyId('');
    setDialogOpen(true);
  };

  /**
   * Open edit dialog
   */
  const handleEdit = (profile: WeightProfile) => {
    setEditingProfile(profile);
    const profileWeights: RankingFeatureWeights = {
      skill_match_weight: profile.skill_match_weight,
      experience_weight: profile.experience_weight,
      education_weight: profile.education_weight,
      location_weight: profile.location_weight,
      keyword_weight: profile.keyword_weight,
      tfidf_weight: profile.tfidf_weight,
      vector_weight: profile.vector_weight,
      recency_weight: profile.recency_weight,
      culture_fit_weight: profile.culture_fit_weight,
      salary_match_weight: profile.salary_match_weight,
      availability_weight: profile.availability_weight,
      certifications_weight: profile.certifications_weight,
      industry_experience_weight: profile.industry_experience_weight,
    };
    setFormData({
      name: profile.name,
      description: profile.description || '',
      ...profileWeights,
      is_default: profile.is_default,
    });
    setBaselineWeights(profileWeights);
    setPreviewVacancyId('');
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
      skill_match_weight: preset.skill_match_weight,
      experience_weight: preset.experience_weight,
      education_weight: preset.education_weight,
      location_weight: preset.location_weight,
      keyword_weight: preset.keyword_weight,
      tfidf_weight: preset.tfidf_weight,
      vector_weight: preset.vector_weight,
      recency_weight: preset.recency_weight,
      culture_fit_weight: preset.culture_fit_weight,
      salary_match_weight: preset.salary_match_weight,
      availability_weight: preset.availability_weight,
      certifications_weight: preset.certifications_weight,
      industry_experience_weight: preset.industry_experience_weight,
      description: preset.description,
    });
  };

  /**
   * Handle weight changes from RankingFeaturesEditor
   */
  const handleWeightsChange = (weights: RankingFeatureWeights) => {
    setFormData({ ...formData, ...weights });
  };

  /**
   * Submit form (create or update)
   */
  const handleSubmit = async () => {
    setSubmitting(true);
    setError(null);

    try {
      // Weights are already normalized by RankingFeaturesEditor
      const submitData = {
        ...formData,
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
        ...DEFAULT_RANKING_WEIGHTS,
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
   * Get top N weights from a profile for display
   */
  const getTopWeights = (profile: WeightProfile, limit: number = 5) => {
    const weights = [
      { label: 'Skills', value: profile.skill_match_weight },
      { label: 'Experience', value: profile.experience_weight },
      { label: 'Education', value: profile.education_weight },
      { label: 'Location', value: profile.location_weight },
      { label: 'Keyword', value: profile.keyword_weight },
      { label: 'TF-IDF', value: profile.tfidf_weight },
      { label: 'Vector', value: profile.vector_weight },
      { label: 'Recency', value: profile.recency_weight },
      { label: 'Culture Fit', value: profile.culture_fit_weight },
      { label: 'Salary', value: profile.salary_match_weight },
      { label: 'Availability', value: profile.availability_weight },
      { label: 'Certs', value: profile.certifications_weight },
      { label: 'Industry', value: profile.industry_experience_weight },
    ];
    return weights
      .sort((a, b) => b.value - a.value)
      .slice(0, limit)
      .filter(w => w.value > 0);
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
                        Top Ranking Features
                      </Typography>
                      <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 0.5 }}>
                        {getTopWeights(profile, 5).map((weight, idx) => (
                          <Chip
                            key={weight.label}
                            label={`${weight.label}: ${Math.round(weight.value * 100)}%`}
                            size="small"
                            variant="outlined"
                          />
                        ))}
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
                        Top Ranking Features
                      </Typography>
                      <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 0.5 }}>
                        {getTopWeights(profile, 5).map((weight, idx) => (
                          <Chip
                            key={weight.label}
                            label={`${weight.label}: ${Math.round(weight.value * 100)}%`}
                            size="small"
                            variant="filled"
                            color={idx === 0 ? 'primary' : idx === 1 ? 'secondary' : 'default'}
                          />
                        ))}
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
        maxWidth="lg"
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

            {/* Ranking Features Editor */}
            <RankingFeaturesEditor
              weights={{
                skill_match_weight: formData.skill_match_weight,
                experience_weight: formData.experience_weight,
                education_weight: formData.education_weight,
                location_weight: formData.location_weight,
                keyword_weight: formData.keyword_weight,
                tfidf_weight: formData.tfidf_weight,
                vector_weight: formData.vector_weight,
                recency_weight: formData.recency_weight,
                culture_fit_weight: formData.culture_fit_weight,
                salary_match_weight: formData.salary_match_weight,
                availability_weight: formData.availability_weight,
                certifications_weight: formData.certifications_weight,
                industry_experience_weight: formData.industry_experience_weight,
              }}
              onChange={handleWeightsChange}
              disabled={submitting}
              showValidation={true}
            />

            {/* Real-time Preview Section */}
            <Divider sx={{ my: 2 }} />

            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Real-time Preview (Optional):
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Enter a vacancy ID to see how weight changes affect candidate rankings in real-time
              </Typography>
              <TextField
                label="Vacancy ID for Preview"
                fullWidth
                value={previewVacancyId}
                onChange={(e) => setPreviewVacancyId(e.target.value)}
                placeholder="e.g., vacancy-123"
                disabled={submitting}
                helperText="Leave empty to skip preview"
              />
            </Box>

            {/* Show preview when vacancy ID is provided */}
            {previewVacancyId && (
              <Box sx={{ mt: 2 }}>
                <MatchingWeightsPreview
                  vacancyId={previewVacancyId}
                  baselineWeights={baselineWeights}
                  modifiedWeights={{
                    skill_match_weight: formData.skill_match_weight,
                    experience_weight: formData.experience_weight,
                    education_weight: formData.education_weight,
                    location_weight: formData.location_weight,
                    keyword_weight: formData.keyword_weight,
                    tfidf_weight: formData.tfidf_weight,
                    vector_weight: formData.vector_weight,
                    recency_weight: formData.recency_weight,
                    culture_fit_weight: formData.culture_fit_weight,
                    salary_match_weight: formData.salary_match_weight,
                    availability_weight: formData.availability_weight,
                    certifications_weight: formData.certifications_weight,
                    industry_experience_weight: formData.industry_experience_weight,
                  }}
                />
              </Box>
            )}
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
