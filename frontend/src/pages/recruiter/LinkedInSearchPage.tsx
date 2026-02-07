import React from 'react';
import { Container, Typography, Box } from '@mui/material';
import { useTranslation } from 'react-i18next';
import LinkedInSearch from '@/components/LinkedInSearch';

const LinkedInSearchPage: React.FC = () => {
  const { t } = useTranslation();

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        {t('linkedin.search.title', 'LinkedIn Search')}
      </Typography>
      <LinkedInSearch />
    </Container>
  );
};

export default LinkedInSearchPage;
