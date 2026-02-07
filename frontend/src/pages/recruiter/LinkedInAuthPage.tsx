import React from 'react';
import { Container, Typography, Box } from '@mui/material';
import { useTranslation } from 'react-i18next';
import LinkedInAuthButton from '@/components/LinkedInAuthButton';

const LinkedInAuthPage: React.FC = () => {
  const { t } = useTranslation();

  return (
    <Container maxWidth="md" sx={{ mt: 8 }}>
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          {t('linkedin.auth.title', 'LinkedIn Authentication')}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {t('linkedin.auth.description', 'Connect your LinkedIn account to enable profile import and job search features.')}
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <LinkedInAuthButton />
      </Box>
    </Container>
  );
};

export default LinkedInAuthPage;
