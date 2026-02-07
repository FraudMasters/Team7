import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Chip,
} from '@mui/material';
import {
  Compare as CompareIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material';
import ModelVersionComparison from '@components/ModelVersionComparison';

/**
 * Model version interface for dropdown
 */
interface ModelVersionOption {
  id: string;
  version: string;
  model_name: string;
  is_active: boolean;
  performance_score: number | null;
  created_at: string;
}

/**
 * Model Versions Page (Admin)
 *
 * Admin dashboard for comparing model versions using A/B testing.
 * Allows selection of two model versions and displays comprehensive
 * performance metrics comparison.
 */
const ModelVersionsPage: React.FC = () => {
  const [modelVersions, setModelVersions] = useState<ModelVersionOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedModelName, setSelectedModelName] = useState<string>('skill_matching');
  const [versionA, setVersionA] = useState<string>('');
  const [versionB, setVersionB] = useState<string>('');

  /**
   * Fetch available model versions
   */
  const fetchModelVersions = async () => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:8000/api/model-versions/?model_name=${selectedModelName}`);
      if (!response.ok) {
        throw new Error('Failed to fetch model versions');
      }
      const data = await response.json();
      setModelVersions(data.models || []);

      // Auto-select active version as version A and latest as version B
      const activeVersion = data.models?.find((v: ModelVersionOption) => v.is_active);
      const versions = data.models || [];
      if (activeVersion) {
        setVersionA(activeVersion.id);
      }
      if (versions.length > 1) {
        const latestVersion = versions[0];
        if (latestVersion.id !== activeVersion?.id) {
          setVersionB(latestVersion.id);
        } else if (versions.length > 1) {
          setVersionB(versions[1].id);
        }
      }
    } catch (error) {
      console.error('Error fetching model versions:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModelVersions();
  }, [selectedModelName]);

  /**
   * Handle model name change
   */
  const handleModelChange = (modelName: string) => {
    setSelectedModelName(modelName);
    setVersionA('');
    setVersionB('');
  };

  const filteredVersions = modelVersions.filter(v => v.model_name === selectedModelName);

  return (
    <Container maxWidth="xl" sx={{ py: 4 }} className="model-versions-page">
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
          <CompareIcon sx={{ fontSize: 32, color: 'primary.main' }} />
          <Box>
            <Typography variant="h4" component="h1" fontWeight={700} gutterBottom>
              Model Version Comparison
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Compare different model versions using A/B testing results
            </Typography>
          </Box>
        </Box>
      </Box>

      {/* Controls Panel */}
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>
          Select Versions to Compare
        </Typography>

        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12} md={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Model</InputLabel>
              <Select
                value={selectedModelName}
                label="Model"
                onChange={(e) => handleModelChange(e.target.value)}
              >
                <MenuItem value="skill_matching">Skill Matching</MenuItem>
                <MenuItem value="ranking">Ranking</MenuItem>
                <MenuItem value="resume_parser">Resume Parser</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} md={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Version A (Baseline)</InputLabel>
              <Select
                value={versionA}
                label="Version A (Baseline)"
                onChange={(e) => setVersionA(e.target.value)}
                disabled={filteredVersions.length === 0}
              >
                {filteredVersions.map((v) => (
                  <MenuItem key={v.id} value={v.id}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <span>{v.version}</span>
                      {v.is_active && (
                        <Chip label="Active" size="small" color="success" variant="outlined" />
                      )}
                      {v.performance_score !== null && (
                        <Chip label={`${v.performance_score.toFixed(0)}`} size="small" color="primary" variant="outlined" />
                      )}
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} md={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Version B (Comparison)</InputLabel>
              <Select
                value={versionB}
                label="Version B (Comparison)"
                onChange={(e) => setVersionB(e.target.value)}
                disabled={filteredVersions.length === 0}
              >
                {filteredVersions.map((v) => (
                  <MenuItem key={v.id} value={v.id}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <span>{v.version}</span>
                      {v.is_active && (
                        <Chip label="Active" size="small" color="success" variant="outlined" />
                      )}
                      {v.performance_score !== null && (
                        <Chip label={`${v.performance_score.toFixed(0)}`} size="small" color="secondary" variant="outlined" />
                      )}
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        </Grid>

        {loading && (
          <Box sx={{ mt: 2, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              Loading model versions...
            </Typography>
          </Box>
        )}

        {!loading && filteredVersions.length === 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary">
              No model versions found for {selectedModelName}. Create some versions first.
            </Typography>
          </Box>
        )}

        {!loading && filteredVersions.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Found {filteredVersions.length} versions for {selectedModelName}
            </Typography>
          </Box>
        )}
      </Paper>

      {/* Comparison Display */}
      {versionA && versionB && versionA !== versionB && (
        <ModelVersionComparison
          versionAId={versionA}
          versionBId={versionB}
          modelName={selectedModelName}
        />
      )}

      {versionA && versionB && versionA === versionB && (
        <Paper elevation={1} sx={{ p: 4, textAlign: 'center' }}>
          <SpeedIcon sx={{ fontSize: 48, color: 'warning.main', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            Please select two different versions to compare
          </Typography>
        </Paper>
      )}
    </Container>
  );
};

export default ModelVersionsPage;
