import React from 'react';
import { Typography, Box } from '@mui/material';
import { useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import AnalysisResults from '@components/AnalysisResults';

/**
 * Results Page Component
 *
 * Displays comprehensive resume analysis results including:
 * - Error detection with severity badges
 * - Grammar and spelling checking
 * - Keyword and skill extraction
 * - Experience summary
 * - Skill highlighting (green for matched, red for missing)
 */
const ResultsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { t } = useTranslation();

  if (!id) {
    return (
      <Box>
        <Typography variant="h4" component="h1" gutterBottom fontWeight={600}>
          {t('results.title')}
        </Typography>
        <Typography variant="body1" color="error.main">
          {t('results.noResumeId')}
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom fontWeight={600}>
        {t('results.title')}
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        {t('results.resumeId', { id })}
      </Typography>

      <AnalysisResults resumeId={id} />
    </Box>
  );
};

export default ResultsPage;
