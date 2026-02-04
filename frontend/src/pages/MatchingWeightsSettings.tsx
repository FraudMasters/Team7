import React from 'react';
import { Container, Typography, Box } from '@/components/ui';
import { useTranslation } from 'react-i18next';
import MatchingWeightsEditor from '@components/MatchingWeightsEditor';

/**
 * Matching Weights Settings Page
 *
 * Provides a recruiter interface for managing organization-specific matching algorithm
 * weight profiles. This page is accessible at /recruiter/settings/matching-weights
 * and requires organization context.
 */
const MatchingWeightsSettingsPage: React.FC = () => {
  const { t } = useTranslation();
  // For now, use a default organization ID
  // In production, this would come from authentication context
  const organizationId = 'org123';

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          {t('matchingWeights.title', { defaultValue: 'Matching Algorithm Weights' })}
        </Typography>
        <Typography variant="body1" color="secondary">
          {t('matchingWeights.subtitle', { defaultValue: 'Customize how candidate-vacancy matching algorithms are weighted for your organization' })}
        </Typography>
      </Box>

      <MatchingWeightsEditor organizationId={organizationId} />
    </Container>
  );
};

export default MatchingWeightsSettingsPage;
