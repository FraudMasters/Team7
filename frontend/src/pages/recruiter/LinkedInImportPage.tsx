import React from 'react';
import { Container, Typography, Box } from '@mui/material';
import { useTranslation } from 'react-i18next';
import LinkedInImport from '@/components/LinkedInImport';

const LinkedInImportPage: React.FC = () => {
  const { t } = useTranslation();

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        {t('linkedin.import.title', 'Import from LinkedIn')}
      </Typography>
      <LinkedInImport />
    </Container>
  );
};

export default LinkedInImportPage;
