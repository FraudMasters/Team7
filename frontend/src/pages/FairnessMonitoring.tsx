import React from 'react';
import { Container, Paper, Typography, Box, Tabs, Tab } from '@/components/ui';
import { useTranslation } from 'react-i18next';
import FairnessDashboard from '@components/analytics/FairnessDashboard';
import FairnessReport from '@components/analytics/FairnessReport';

/**
 * FairnessMonitoringPage Component
 *
 * Admin page for monitoring AI bias detection and fairness metrics.
 * Integrates dashboard overview and detailed fairness analysis reports.
 */
const FairnessMonitoringPage: React.FC = () => {
  const { t } = useTranslation();
  const [currentTab, setCurrentTab] = React.useState(0);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          {t('fairnessMonitoring.title')}
        </Typography>
        <Typography variant="body1" color="secondary">
          {t('fairnessMonitoring.subtitle')}
        </Typography>
      </Box>

      <Paper elevation={1} sx={{ p: 0 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={currentTab} onChange={handleTabChange}>
            <Tab label={t('fairnessMonitoring.tabs.dashboard')} />
            <Tab label={t('fairnessMonitoring.tabs.report')} />
          </Tabs>
        </Box>

        <Box sx={{ p: 0 }}>
          {currentTab === 0 && (
            <Box>
              <FairnessDashboard />
            </Box>
          )}
          {currentTab === 1 && (
            <Box>
              <FairnessReport />
            </Box>
          )}
        </Box>
      </Paper>
    </Container>
  );
};

export default FairnessMonitoringPage;
