import React from 'react';
import { Container, Paper, Typography, Box } from '@mui/material';
import { useTranslation } from 'react-i18next';
import FeedbackAnalytics from '@components/FeedbackAnalytics';

/**
 * AdminAnalyticsPage Component
 *
 * Admin page for viewing feedback analytics dashboard with match accuracy
 * and learning progress metrics.
 */
const AdminAnalyticsPage: React.FC = () => {
  const { t } = useTranslation();

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          {t('adminAnalytics.title')}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {t('adminAnalytics.subtitle')}
        </Typography>
      </Box>

      <Paper elevation={1} sx={{ p: 0 }}>
        <FeedbackAnalytics />
      </Paper>
    </Container>
  );
};

export default AdminAnalyticsPage;
