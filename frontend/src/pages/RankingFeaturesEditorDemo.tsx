import React, { useState } from 'react';
import { Container, Box, Typography, Paper, Button, Stack } from '@mui/material';
import { useTranslation } from 'react-i18next';
import RankingFeaturesEditor, {
  RankingFeatureWeights,
  DEFAULT_RANKING_WEIGHTS,
} from '@components/RankingFeaturesEditor';
import { Refresh as RefreshIcon } from '@mui/icons-material';

/**
 * Demo page for RankingFeaturesEditor component
 *
 * This page is for testing and verification purposes, showing the
 * RankingFeaturesEditor with all 13 weight sliders functional.
 */
const RankingFeaturesEditorDemo: React.FC = () => {
  const { t } = useTranslation();
  const [weights, setWeights] = useState<RankingFeatureWeights>(DEFAULT_RANKING_WEIGHTS);

  const handleReset = () => {
    setWeights(DEFAULT_RANKING_WEIGHTS);
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Ranking Features Editor Demo
        </Typography>
        <Typography variant="body1" color="text.secondary" gutterBottom>
          Test and verify the 13 ranking feature weight sliders
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={handleReset}
          sx={{ mt: 2 }}
        >
          Reset to Defaults
        </Button>
      </Box>

      <Paper elevation={2} sx={{ p: 4 }}>
        <RankingFeaturesEditor
          weights={weights}
          onChange={setWeights}
          showValidation={true}
        />
      </Paper>

      <Paper elevation={1} sx={{ p: 3, mt: 3, bgcolor: 'grey.50' }}>
        <Typography variant="h6" gutterBottom>
          Current Weights (Raw Values)
        </Typography>
        <Stack spacing={0.5}>
          {Object.entries(weights).map(([key, value]) => (
            <Typography key={key} variant="body2" fontFamily="monospace">
              {key}: {value.toFixed(4)}
            </Typography>
          ))}
        </Stack>
      </Paper>
    </Container>
  );
};

export default RankingFeaturesEditorDemo;
