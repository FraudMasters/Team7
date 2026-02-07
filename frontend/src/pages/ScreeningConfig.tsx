import React from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  Breadcrumbs,
  Link,
  Stack,
} from '@mui/material';
import { useNavigate, useParams, Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import ScreeningConfig from '@/components/ScreeningConfig';
import type { ScreeningRule } from '@/types/api';

/**
 * Screening Configuration Page
 *
 * Provides a page wrapper for the ScreeningConfig component.
 * Displays the screening rule configuration form for a specific vacancy.
 *
 * @example
 * ```tsx
 * // Route: /screening/config/:vacancyId
 * <ScreeningConfigPage />
 * ```
 */
const ScreeningConfigPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { vacancyId } = useParams<{ vacancyId: string }>();

  /**
   * Handle successful rule save
   */
  const handleSaveSuccess = (rule: ScreeningRule) => {
    console.log('Screening rule saved successfully:', rule);
    // Optionally navigate back to vacancy detail or stay on page
    // navigate(`/recruiter/vacancies/${vacancyId}`);
  };

  /**
   * Handle back navigation
   */
  const handleBack = () => {
    if (vacancyId) {
      navigate(`/recruiter/vacancies/${vacancyId}`);
    } else {
      navigate('/recruiter/vacancies');
    }
  };

  if (!vacancyId) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Paper elevation={1} sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="error">
            {t('screeningConfig.errors.noVacancyId', 'No vacancy ID provided')}
          </Typography>
        </Paper>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Page Header */}
      <Stack spacing={2} sx={{ mb: 3 }}>
        {/* Breadcrumbs */}
        <Breadcrumbs aria-label="breadcrumb">
          <Link component={RouterLink} to="/recruiter/dashboard" underline="hover" color="inherit">
            {t('common.dashboard', 'Dashboard')}
          </Link>
          <Link component={RouterLink} to="/recruiter/vacancies" underline="hover" color="inherit">
            {t('common.vacancies', 'Vacancies')}
          </Link>
          <Link
            component={RouterLink}
            to={`/recruiter/vacancies/${vacancyId}`}
            underline="hover"
            color="inherit"
          >
            {t('common.vacancyDetails', 'Vacancy Details')}
          </Link>
          <Typography color="text.primary">
            {t('screeningConfig.pageTitle', 'Screening Configuration')}
          </Typography>
        </Breadcrumbs>

        {/* Page Title */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="h4" fontWeight={700} gutterBottom>
              {t('screeningConfig.pageHeading', 'Screening Rule Configuration')}
            </Typography>
            <Typography variant="body1" color="text.secondary">
              {t('screeningConfig.pageDescription', 'Configure automated screening rules for this vacancy')}
            </Typography>
          </Box>
        </Box>
      </Stack>

      {/* Screening Config Component */}
      <ScreeningConfig
        vacancyId={vacancyId}
        onSaveSuccess={handleSaveSuccess}
      />
    </Container>
  );
};

export default ScreeningConfigPage;
