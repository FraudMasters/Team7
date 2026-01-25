import React from 'react';
import { Container, Typography, Box } from '@mui/material';
import CustomSynonymsManager from '@components/CustomSynonymsManager';

/**
 * Admin Synonyms Page
 *
 * Provides an admin interface for managing organization-specific custom skill synonyms.
 * This page is accessible at /admin/synonyms and requires organization context.
 */
const AdminSynonymsPage: React.FC = () => {
  // For now, use a default organization ID
  // In production, this would come from authentication context
  const organizationId = 'org123';

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Custom Synonyms Management
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage organization-specific custom skill synonym mappings to improve matching accuracy.
        </Typography>
      </Box>

      <CustomSynonymsManager organizationId={organizationId} />
    </Container>
  );
};

export default AdminSynonymsPage;
