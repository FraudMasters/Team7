import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Grid,
  Stack,
  Button,
  CircularProgress,
  Alert,
  Divider,
  Switch,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Chip,
  Tooltip,
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';

type ExplanationTone = 'professional' | 'relaxed' | 'friendly' | 'formal';
type ExplanationStyle = 'detailed' | 'concise' | 'balanced';
type DetailLevel = 'high' | 'medium' | 'low';

interface ExplanationPreferences {
  id: string;
  organization_id: string;
  tone: ExplanationTone;
  style: ExplanationStyle;
  detail_level: DetailLevel;
  include_percentiles: boolean;
  include_skill_names: boolean;
  include_experience_details: boolean;
  include_education_details: boolean;
  language: string | null;
  custom_prompt_template: string | null;
  is_active: boolean;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

interface UpdatePreferencesRequest {
  tone?: ExplanationTone;
  style?: ExplanationStyle;
  detail_level?: DetailLevel;
  include_percentiles?: boolean;
  include_skill_names?: boolean;
  include_experience_details?: boolean;
  include_education_details?: boolean;
  language?: string;
  custom_prompt_template?: string;
  is_active?: boolean;
}

interface ExplanationPreferencesProps {
  organizationId: string;
  apiUrl?: string;
  onSave?: (preferences: ExplanationPreferences) => void;
  onError?: (error: string) => void;
}

const DEFAULT_PREFERENCES = {
  tone: 'professional' as ExplanationTone,
  style: 'balanced' as ExplanationStyle,
  detail_level: 'medium' as DetailLevel,
  include_percentiles: true,
  include_skill_names: true,
  include_experience_details: true,
  include_education_details: true,
  language: 'en',
  custom_prompt_template: null,
  is_active: false,
};

const TONE_DESCRIPTIONS: Record<ExplanationTone, string> = {
  professional: 'Formal and business-oriented explanations suitable for corporate environments',
  relaxed: 'Relaxed and friendly explanations for startups and workplaces',
  friendly: 'Warm and approachable explanations that maintain professionalism',
  formal: 'Strictly formal explanations suitable for regulated industries',
};

const STYLE_DESCRIPTIONS: Record<ExplanationStyle, string> = {
  detailed: 'Comprehensive explanations with extensive context',
  concise: 'Brief explanations focusing on key insights',
  balanced: 'Middle-ground approach with adequate detail',
};

const DETAIL_DESCRIPTIONS: Record<DetailLevel, string> = {
  high: 'Maximum detail with all available information',
  medium: 'Standard detail level with key information highlighted',
  low: 'Essential information only for quick scanning',
};

const ExplanationPreferences: React.FC<ExplanationPreferencesProps> = ({
  organizationId,
  apiUrl = '/api/explainability',
  onSave,
  onError,
}) => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [preferences, setPreferences] = useState<ExplanationPreferences | null>(null);
  const [hasChanges, setHasChanges] = useState(false);
  const [localPrefs, setLocalPrefs] = useState<UpdatePreferencesRequest>({});

  const fetchPreferences = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${apiUrl}/preferences/${organizationId}`);
      if (!response.ok) throw new Error(`Failed to fetch: ${response.statusText}`);
      const data: ExplanationPreferences = await response.json();
      setPreferences(data);
      setLocalPrefs({
        tone: data.tone,
        style: data.style,
        detail_level: data.detail_level,
        include_percentiles: data.include_percentiles,
        include_skill_names: data.include_skill_names,
        include_experience_details: data.include_experience_details,
        include_education_details: data.include_education_details,
        language: data.language || undefined,
        custom_prompt_template: data.custom_prompt_template || undefined,
        is_active: data.is_active,
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load preferences';
      setError(errorMessage);
      onError?.(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (organizationId) fetchPreferences();
  }, [organizationId, apiUrl]);

  const handleSave = async () => {
    if (!hasChanges) return;
    setSaving(true);
    setError(null);
    setSuccess(false);
    try {
      const response = await fetch(`${apiUrl}/preferences/${organizationId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(localPrefs),
      });
      if (!response.ok) throw new Error(`Failed to save: ${response.statusText}`);
      const data: ExplanationPreferences = await response.json();
      setPreferences(data);
      setHasChanges(false);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
      onSave?.(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save preferences';
      setError(errorMessage);
      onError?.(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    if (preferences) {
      setLocalPrefs({
        tone: preferences.tone,
        style: preferences.style,
        detail_level: preferences.detail_level,
        include_percentiles: preferences.include_percentiles,
        include_skill_names: preferences.include_skill_names,
        include_experience_details: preferences.include_experience_details,
        include_education_details: preferences.include_education_details,
        language: preferences.language || undefined,
        custom_prompt_template: preferences.custom_prompt_template || undefined,
        is_active: preferences.is_active,
      });
      setHasChanges(false);
      setError(null);
    }
  };

  const updateLocalPref = <K extends keyof UpdatePreferencesRequest>(
    key: K,
    value: UpdatePreferencesRequest[K]
  ) => {
    setLocalPrefs(prev => ({ ...prev, [key]: value }));
    setHasChanges(true);
    setSuccess(false);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', py: 8 }}>
        <CircularProgress size={48} sx={{ mb: 2 }} />
        <Typography variant="body1" color="text.secondary">Loading preferences...</Typography>
      </Box>
    );
  }

  return (
    <Stack spacing={3}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Icon name="settings" sx={{ fontSize: 28, color: 'primary.main' }} />
          <Typography variant="h5" fontWeight={700}>AI Explanation Settings</Typography>
        </Box>
        {hasChanges && <Chip label="Unsaved changes" color="warning" size="small" />}
      </Box>

      {error && <Alert severity="error" onClose={() => setError(null)}>{error}</Alert>}
      {success && <Alert severity="success" onClose={() => setSuccess(false)}>Settings saved successfully!</Alert>}

      <Paper elevation={2} sx={{ p: 3 }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>Tone and Style</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Configure how AI explains candidate ranking decisions
        </Typography>

        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Tone</InputLabel>
              <Select
                value={localPrefs.tone || DEFAULT_PREFERENCES.tone}
                label="Tone"
                onChange={(e) => updateLocalPref('tone', e.target.value as ExplanationTone)}
              >
                <MenuItem value="professional">Professional</MenuItem>
                <MenuItem value="relaxed">Relaxed</MenuItem>
                <MenuItem value="friendly">Friendly</MenuItem>
                <MenuItem value="formal">Formal</MenuItem>
              </Select>
            </FormControl>
            {localPrefs.tone && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                {TONE_DESCRIPTIONS[localPrefs.tone as ExplanationTone]}
              </Typography>
            )}
          </Grid>

          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Style</InputLabel>
              <Select
                value={localPrefs.style || DEFAULT_PREFERENCES.style}
                label="Style"
                onChange={(e) => updateLocalPref('style', e.target.value as ExplanationStyle)}
              >
                <MenuItem value="detailed">Detailed</MenuItem>
                <MenuItem value="concise">Concise</MenuItem>
                <MenuItem value="balanced">Balanced</MenuItem>
              </Select>
            </FormControl>
            {localPrefs.style && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                {STYLE_DESCRIPTIONS[localPrefs.style as ExplanationStyle]}
              </Typography>
            )}
          </Grid>

          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Detail Level</InputLabel>
              <Select
                value={localPrefs.detail_level || DEFAULT_PREFERENCES.detail_level}
                label="Detail Level"
                onChange={(e) => updateLocalPref('detail_level', e.target.value as DetailLevel)}
              >
                <MenuItem value="high">High</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
                <MenuItem value="low">Low</MenuItem>
              </Select>
            </FormControl>
            {localPrefs.detail_level && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                {DETAIL_DESCRIPTIONS[localPrefs.detail_level as DetailLevel]}
              </Typography>
            )}
          </Grid>
        </Grid>
      </Paper>

      <Paper elevation={2} sx={{ p: 3 }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>Content Inclusion</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Select what information to include in explanations
        </Typography>

        <Stack spacing={2}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ flex: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Icon name="bar-chart" sx={{ fontSize: 20, color: 'primary.main' }} />
                <Typography variant="body1" fontWeight={600}>Percentiles</Typography>
              </Box>
              <Typography variant="caption" color="text.secondary">
                Include comparison with other candidates
              </Typography>
            </Box>
            <Switch
              checked={localPrefs.include_percentiles ?? DEFAULT_PREFERENCES.include_percentiles}
              onChange={(e) => updateLocalPref('include_percentiles', e.target.checked)}
            />
          </Box>

          <Divider />

          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ flex: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Icon name="code" sx={{ fontSize: 20, color: 'primary.main' }} />
                <Typography variant="body1" fontWeight={600}>Skills</Typography>
              </Box>
              <Typography variant="caption" color="text.secondary">
                Include specific skill names in explanations
              </Typography>
            </Box>
            <Switch
              checked={localPrefs.include_skill_names ?? DEFAULT_PREFERENCES.include_skill_names}
              onChange={(e) => updateLocalPref('include_skill_names', e.target.checked)}
            />
          </Box>

          <Divider />

          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ flex: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Icon name="work" sx={{ fontSize: 20, color: 'primary.main' }} />
                <Typography variant="body1" fontWeight={600}>Experience</Typography>
              </Box>
              <Typography variant="caption" color="text.secondary">
                Include work experience duration details
              </Typography>
            </Box>
            <Switch
              checked={localPrefs.include_experience_details ?? DEFAULT_PREFERENCES.include_experience_details}
              onChange={(e) => updateLocalPref('include_experience_details', e.target.checked)}
            />
          </Box>

          <Divider />

          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ flex: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Icon name="school" sx={{ fontSize: 20, color: 'primary.main' }} />
                <Typography variant="body1" fontWeight={600}>Education</Typography>
              </Box>
              <Typography variant="caption" color="text.secondary">
                Include education details
              </Typography>
            </Box>
            <Switch
              checked={localPrefs.include_education_details ?? DEFAULT_PREFERENCES.include_education_details}
              onChange={(e) => updateLocalPref('include_education_details', e.target.checked)}
            />
          </Box>
        </Stack>
      </Paper>

      <Paper elevation={2} sx={{ p: 3 }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>Advanced Settings</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Language and additional parameters
        </Typography>

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Language</InputLabel>
              <Select
                value={localPrefs.language || DEFAULT_PREFERENCES.language || 'en'}
                label="Language"
                onChange={(e) => updateLocalPref('language', e.target.value)}
              >
                <MenuItem value="en">🇬🇧 English</MenuItem>
                <MenuItem value="ru">🇷🇺 Русский</MenuItem>
                <MenuItem value="es">🇪🇸 Español</MenuItem>
                <MenuItem value="fr">🇫🇷 Français</MenuItem>
                <MenuItem value="de">🇩🇪 Deutsch</MenuItem>
              </Select>
            </FormControl>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              Language for AI-generated explanations
            </Typography>
          </Grid>

          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: '100%' }}>
              <Box sx={{ flex: 1 }}>
                <Typography variant="body1" fontWeight={600} gutterBottom>Active Settings</Typography>
                <Typography variant="caption" color="text.secondary">
                  Use these settings for generating explanations
                </Typography>
              </Box>
              <Switch
                checked={localPrefs.is_active ?? DEFAULT_PREFERENCES.is_active}
                onChange={(e) => updateLocalPref('is_active', e.target.checked)}
                color="success"
              />
            </Box>
          </Grid>
        </Grid>

        <Box sx={{ mt: 3 }}>
          <Typography variant="subtitle2" fontWeight={600} gutterBottom>
            Custom Prompt Template (Optional)
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
            Optional custom template for LLM explanations. Leave empty for standard template.
          </Typography>
          <TextField
            fullWidth
            multiline
            rows={4}
            placeholder="Enter custom prompt template..."
            value={localPrefs.custom_prompt_template || ''}
            onChange={(e) => updateLocalPref('custom_prompt_template', e.target.value || null)}
            helperText="Use {{candidate_name}}, {{rank_score}}, and other variables in the template"
          />
        </Box>
      </Paper>

      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
        <Button
          variant="outlined"
          onClick={handleReset}
          disabled={!hasChanges || saving}
          startIcon={<Icon name="refresh" />}
        >
          Reset
        </Button>
        <Button
          variant="contained"
          onClick={handleSave}
          disabled={!hasChanges || saving}
          startIcon={saving ? <CircularProgress size={16} /> : <Icon name="save" />}
        >
          {saving ? 'Saving...' : 'Save Settings'}
        </Button>
      </Box>

      {preferences && (
        <Paper elevation={1} sx={{ p: 2, bgcolor: 'action.hover' }}>
          <Typography variant="caption" color="text.secondary">
            <strong>Last updated:</strong> {new Date(preferences.updated_at).toLocaleString()}
            {' • '}
            <strong>Tone:</strong> {preferences.tone}
            {' • '}
            <strong>Style:</strong> {preferences.style}
            {' • '}
            <strong>Detail:</strong> {preferences.detail_level}
          </Typography>
        </Paper>
      )}
    </Stack>
  );
};

export default ExplanationPreferences;
