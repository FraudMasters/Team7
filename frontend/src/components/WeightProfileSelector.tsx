import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
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
  CircularProgress,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  RadioGroup,
  Radio,
  FormControlLabel,
  Button,
  Tooltip,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Info as InfoIcon,
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
 * WeightProfileSelector Component Props
 */
interface WeightProfileSelectorProps {
  /** Organization ID to fetch profiles for */
  organizationId: string;
  /** Currently selected profile ID */
  selectedProfileId?: string;
  /** Callback when profile is selected */
  onProfileSelect?: (profile: WeightProfile) => void;
  /** API endpoint URL for matching weights */
  apiUrl?: string;
  /** Whether to show preset profiles only */
  presetsOnly?: boolean;
  /** Whether to show custom profiles only */
  customOnly?: boolean;
  /** Whether to allow clearing selection */
  allowClear?: boolean;
  /** Compact mode for inline display */
  compact?: boolean;
  /** Disabled state */
  disabled?: boolean;
}

/**
 * Preset profile definitions for fallback display
 */
const PRESET_PROFILES: Record<string, { name: string; description: string; color: string }> = {
  technical: {
    name: 'Technical',
    description: 'Emphasizes exact keyword matching for technical roles',
    color: 'primary',
  },
  creative: {
    name: 'Creative',
    description: 'Prioritizes semantic understanding for creative roles',
    color: 'secondary',
  },
  executive: {
    name: 'Executive',
    description: 'Balanced approach for leadership positions',
    color: 'warning',
  },
  balanced: {
    name: 'Balanced',
    description: 'Equal weighting for all matching algorithms',
    color: 'info',
  },
};

/**
 * WeightProfileSelector Component
 *
 * Provides a compact interface for selecting matching algorithm weight profiles.
 * Features include:
 * - List all available profiles (preset and custom)
 * - Visual selection indicator
 * - Display weight distribution for each profile
 * - Group profiles by preset/custom
 * - Compact view suitable for embedding in other pages
 * - Callback when profile is selected
 *
 * @example
 * ```tsx
 * <WeightProfileSelector
 *   organizationId="org123"
 *   selectedProfileId="profile-uuid"
 *   onProfileSelect={(profile) => console.log('Selected:', profile)}
 * />
 * ```
 */
const WeightProfileSelector: React.FC<WeightProfileSelectorProps> = ({
  organizationId,
  selectedProfileId,
  onProfileSelect,
  apiUrl = 'http://localhost:8000/api/matching-weights',
  presetsOnly = false,
  customOnly = false,
  allowClear = false,
  compact = false,
  disabled = false,
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [profiles, setProfiles] = useState<WeightProfile[]>([]);

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
   * Handle profile selection
   */
  const handleProfileSelect = (profile: WeightProfile) => {
    if (disabled) return;
    if (onProfileSelect) {
      onProfileSelect(profile);
    }
  };

  /**
   * Handle clearing selection
   */
  const handleClearSelection = () => {
    if (disabled || !allowClear) return;
    if (onProfileSelect) {
      onProfileSelect(null as any);
    }
  };

  /**
   * Get preset type color
   */
  const getPresetColor = (presetType?: string): any => {
    if (!presetType) return 'default';
    return PRESET_PROFILES[presetType]?.color || 'default';
  };

  /**
   * Get preset type info
   */
  const getPresetInfo = (presetType?: string) => {
    if (!presetType) return null;
    return PRESET_PROFILES[presetType] || null;
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
          py: compact ? 2 : 4,
        }}
      >
        <CircularProgress size={compact ? 24 : 40} sx={{ mb: 1 }} />
        <Typography variant={compact ? 'body2' : 'body1'} color="text.secondary">
          Loading profiles...
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
          <Button color="inherit" onClick={fetchProfiles} size="small">
            Retry
          </Button>
        }
      >
        <AlertTitle>Error</AlertTitle>
        {error}
      </Alert>
    );
  }

  // Filter profiles based on props
  let filteredProfiles = profiles;
  if (presetsOnly) {
    filteredProfiles = profiles.filter((p) => p.is_preset);
  } else if (customOnly) {
    filteredProfiles = profiles.filter((p) => !p.is_preset);
  }

  const presetProfiles = filteredProfiles.filter((p) => p.is_preset);
  const customProfiles = filteredProfiles.filter((p) => !p.is_preset);

  /**
   * Compact mode: dropdown selector
   */
  if (compact) {
    return (
      <FormControl fullWidth disabled={disabled}>
        <InputLabel>Weight Profile</InputLabel>
        <Select
          value={selectedProfileId || ''}
          label="Weight Profile"
          onChange={(e) => {
            const profile = profiles.find((p) => p.id === e.target.value);
            if (profile) {
              handleProfileSelect(profile);
            }
          }}
        >
          {allowClear && (
            <MenuItem value="">
              <em>None</em>
            </MenuItem>
          )}
          {presetProfiles.length > 0 && (
            <>
              <MenuItem disabled sx={{ opacity: 0.5, fontStyle: 'italic' }}>
                Preset Profiles
              </MenuItem>
              {presetProfiles.map((profile) => (
                <MenuItem key={profile.id} value={profile.id}>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <Typography variant="body2">{profile.name}</Typography>
                    <Chip
                      label={`K:${Math.round(profile.keyword_weight * 100)}%`}
                      size="small"
                      variant="outlined"
                    />
                  </Stack>
                </MenuItem>
              ))}
            </>
          )}
          {customProfiles.length > 0 && (
            <>
              <MenuItem disabled sx={{ opacity: 0.5, fontStyle: 'italic' }}>
                Custom Profiles
              </MenuItem>
              {customProfiles.map((profile) => (
                <MenuItem key={profile.id} value={profile.id}>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <Typography variant="body2">{profile.name}</Typography>
                    <Chip
                      label={`K:${Math.round(profile.keyword_weight * 100)}%`}
                      size="small"
                      variant="filled"
                    />
                  </Stack>
                </MenuItem>
              ))}
            </>
          )}
        </Select>
      </FormControl>
    );
  }

  /**
   * Full mode: card-based selection
   */
  return (
    <Stack spacing={2}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6" fontWeight={600}>
          Select Weight Profile
        </Typography>
        {allowClear && selectedProfileId && (
          <Button size="small" onClick={handleClearSelection} disabled={disabled}>
            Clear Selection
          </Button>
        )}
      </Box>

      {/* Info Alert */}
      <Alert severity="info" icon={<InfoIcon fontSize="inherit" />}>
        <Typography variant="body2">
          Choose a weight profile to determine how candidates are matched. Different profiles emphasize
          different matching algorithms.
        </Typography>
      </Alert>

      {/* Preset Profiles */}
      {presetProfiles.length > 0 && (
        <Box>
          <Typography variant="subtitle2" fontWeight={600} gutterBottom>
            Preset Profiles
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Pre-configured profiles for common use cases
          </Typography>
          <Grid container spacing={2}>
            {presetProfiles.map((profile) => {
              const isSelected = selectedProfileId === profile.id;
              const presetInfo = getPresetInfo(profile.preset_type);

              return (
                <Grid item xs={12} md={6} key={profile.id}>
                  <Card
                    onClick={() => handleProfileSelect(profile)}
                    sx={{
                      cursor: disabled ? 'not-allowed' : 'pointer',
                      border: isSelected ? 2 : 1,
                      borderColor: isSelected ? 'primary.main' : 'divider',
                      opacity: disabled ? 0.6 : 1,
                      transition: 'all 0.2s',
                      '&:hover': !disabled ? {
                        boxShadow: 4,
                        transform: 'translateY(-2px)',
                      } : {},
                    }}
                  >
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                        <Box sx={{ flex: 1 }}>
                          <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                            <Typography variant="h6" fontWeight={600}>
                              {profile.name}
                            </Typography>
                            {isSelected && (
                              <CheckCircleIcon color="primary" fontSize="small" />
                            )}
                          </Stack>
                          {profile.description && (
                            <Typography variant="body2" color="text.secondary">
                              {profile.description}
                            </Typography>
                          )}
                        </Box>
                        {profile.preset_type && (
                          <Chip
                            label={presetInfo?.name || profile.preset_type}
                            size="small"
                            color={getPresetColor(profile.preset_type)}
                            variant="filled"
                          />
                        )}
                      </Box>

                      <Divider sx={{ my: 1 }} />

                      <Box sx={{ mt: 2 }}>
                        <Typography variant="caption" color="text.secondary" gutterBottom display="block">
                          Algorithm Weights
                        </Typography>
                        <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 0.5 }}>
                          <Tooltip title="Exact keyword and phrase matching">
                            <Chip
                              label={`Keyword: ${Math.round(profile.keyword_weight * 100)}%`}
                              size="small"
                              variant="outlined"
                              color="primary"
                            />
                          </Tooltip>
                          <Tooltip title="Term frequency-inverse document frequency">
                            <Chip
                              label={`TF-IDF: ${Math.round(profile.tfidf_weight * 100)}%`}
                              size="small"
                              variant="outlined"
                              color="secondary"
                            />
                          </Tooltip>
                          <Tooltip title="Semantic vector embeddings similarity">
                            <Chip
                              label={`Vector: ${Math.round(profile.vector_weight * 100)}%`}
                              size="small"
                              variant="outlined"
                              color="info"
                            />
                          </Tooltip>
                        </Stack>
                      </Box>

                      {profile.is_default && (
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
              );
            })}
          </Grid>
        </Box>
      )}

      {/* Custom Profiles */}
      {customProfiles.length > 0 && (
        <Box>
          <Typography variant="subtitle2" fontWeight={600} gutterBottom>
            Custom Profiles
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Organization-specific weight profiles
          </Typography>
          <Grid container spacing={2}>
            {customProfiles.map((profile) => {
              const isSelected = selectedProfileId === profile.id;

              return (
                <Grid item xs={12} md={6} key={profile.id}>
                  <Card
                    onClick={() => handleProfileSelect(profile)}
                    sx={{
                      cursor: disabled ? 'not-allowed' : 'pointer',
                      border: isSelected ? 2 : 1,
                      borderColor: isSelected ? 'primary.main' : 'divider',
                      opacity: disabled ? 0.6 : 1,
                      transition: 'all 0.2s',
                      '&:hover': !disabled ? {
                        boxShadow: 4,
                        transform: 'translateY(-2px)',
                      } : {},
                    }}
                  >
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                        <Box sx={{ flex: 1 }}>
                          <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                            <Typography variant="h6" fontWeight={600}>
                              {profile.name}
                            </Typography>
                            {isSelected && (
                              <CheckCircleIcon color="primary" fontSize="small" />
                            )}
                          </Stack>
                          {profile.description && (
                            <Typography variant="body2" color="text.secondary">
                              {profile.description}
                            </Typography>
                          )}
                        </Box>
                        <Chip
                          label="Custom"
                          size="small"
                          color="default"
                          variant="outlined"
                        />
                      </Box>

                      <Divider sx={{ my: 1 }} />

                      <Box sx={{ mt: 2 }}>
                        <Typography variant="caption" color="text.secondary" gutterBottom display="block">
                          Algorithm Weights
                        </Typography>
                        <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 0.5 }}>
                          <Tooltip title="Exact keyword and phrase matching">
                            <Chip
                              label={`Keyword: ${Math.round(profile.keyword_weight * 100)}%`}
                              size="small"
                              variant="filled"
                              color="primary"
                            />
                          </Tooltip>
                          <Tooltip title="Term frequency-inverse document frequency">
                            <Chip
                              label={`TF-IDF: ${Math.round(profile.tfidf_weight * 100)}%`}
                              size="small"
                              variant="filled"
                              color="secondary"
                            />
                          </Tooltip>
                          <Tooltip title="Semantic vector embeddings similarity">
                            <Chip
                              label={`Vector: ${Math.round(profile.vector_weight * 100)}%`}
                              size="small"
                              variant="filled"
                              color="info"
                            />
                          </Tooltip>
                        </Stack>
                      </Box>

                      {profile.is_default && (
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
              );
            })}
          </Grid>
        </Box>
      )}

      {/* No profiles available */}
      {filteredProfiles.length === 0 && (
        <Paper elevation={1} sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No Weight Profiles Available
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {presetsOnly
              ? 'No preset profiles found'
              : customOnly
              ? 'No custom profiles found. Create one in the Weight Profiles settings'
              : 'No weight profiles available. Create one to get started'}
          </Typography>
        </Paper>
      )}
    </Stack>
  );
};

export default WeightProfileSelector;
