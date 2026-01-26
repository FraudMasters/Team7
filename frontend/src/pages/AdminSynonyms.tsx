import React from 'react';
import { Container, Typography, Box } from '@mui/material';
import { useTranslation } from 'react-i18next';
import CustomSynonymsManager from '@components/CustomSynonymsManager';

/**
 * Admin Synonyms Page
 *
 * Provides an admin interface for managing organization-specific custom skill synonyms.
 * This page is accessible at /admin/synonyms and requires organization context.
 */
const AdminSynonymsPage: React.FC = () => {
  const { t } = useTranslation();
  // For now, use a default organization ID
  // In production, this would come from authentication context
  const organizationId = 'org123';

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          {t('adminSynonyms.title')}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {t('adminSynonyms.subtitle')}
        </Typography>
      </Box>

      <CustomSynonymsManager organizationId={organizationId} />
    </Container>
  );
};

export default AdminSynonymsPage;
