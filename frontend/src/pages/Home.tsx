import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Typography,
  Box,
  Paper,
  Button,
  Grid,
  Card,
  CardContent,
  CardActions,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Analytics as AnalysisIcon,
  CompareArrows as CompareIcon,
  Speed as SpeedIcon,
  Psychology as AIIcon,
  CheckCircle as SuccessIcon,
} from '@mui/icons-material';

/**
 * Home Page Component
 *
 * Landing page with feature overview and call-to-action buttons.
 */
const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();

  const features = [
    {
      icon: <AIIcon fontSize="large" color="primary" />,
      title: t('home.features.aiAnalysis.title'),
      description: t('home.features.aiAnalysis.description'),
    },
    {
      icon: <SuccessIcon fontSize="large" color="success" />,
      title: t('home.features.errorDetection.title'),
      description: t('home.features.errorDetection.description'),
    },
    {
      icon: <CompareIcon fontSize="large" color="secondary" />,
      title: t('home.features.jobMatching.title'),
      description: t('home.features.jobMatching.description'),
    },
    {
      icon: <SpeedIcon fontSize="large" color="info" />,
      title: t('home.features.fastProcessing.title'),
      description: t('home.features.fastProcessing.description'),
    },
  ];

  return (
    <Box>
      {/* Hero Section */}
      <Box sx={{ mb: 6, textAlign: 'center' }}>
        <Typography
          variant="h2"
          component="h1"
          gutterBottom
          sx={{ fontWeight: 700, mb: 2 }}
        >
          {t('home.hero.title')}
        </Typography>
        <Typography variant="h5" color="text.secondary" paragraph sx={{ mb: 4 }}>
          {t('home.hero.subtitle')}
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
          <Button
            variant="contained"
            size="large"
            startIcon={<UploadIcon />}
            onClick={() => navigate('/upload')}
            sx={{ px: 4, py: 1.5, fontSize: '1.1rem' }}
          >
            {t('home.hero.uploadButton')}
          </Button>
          <Button
            variant="outlined"
            size="large"
            startIcon={<AnalysisIcon />}
            onClick={() => navigate('/results')}
            sx={{ px: 4, py: 1.5, fontSize: '1.1rem' }}
          >
            {t('home.hero.viewSampleButton')}
          </Button>
        </Box>
      </Box>

      {/* Features Grid */}
      <Box sx={{ mb: 6 }}>
        <Typography variant="h4" component="h2" gutterBottom align="center" sx={{ mb: 4 }}>
          {t('home.features.title')}
        </Typography>
        <Grid container spacing={3}>
          {features.map((feature, index) => (
            <Grid item xs={12} sm={6} md={3} key={index}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 4,
                  },
                }}
              >
                <CardContent sx={{ flexGrow: 1, textAlign: 'center' }}>
                  <Box sx={{ mb: 2 }}>{feature.icon}</Box>
                  <Typography variant="h6" component="h3" gutterBottom fontWeight={600}>
                    {feature.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {feature.description}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* How It Works Section */}
      <Box sx={{ mb: 6 }}>
        <Typography variant="h4" component="h2" gutterBottom align="center" sx={{ mb: 4 }}>
          {t('home.howItWorks.title')}
        </Typography>
        <Paper elevation={2} sx={{ p: 4 }}>
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} md={4} sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="primary" fontWeight={700}>
                1
              </Typography>
              <Typography variant="h6" gutterBottom>
                {t('home.howItWorks.step1.title')}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t('home.howItWorks.step1.description')}
              </Typography>
            </Grid>
            <Grid item xs={12} md={4} sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="primary" fontWeight={700}>
                2
              </Typography>
              <Typography variant="h6" gutterBottom>
                {t('home.howItWorks.step2.title')}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t('home.howItWorks.step2.description')}
              </Typography>
            </Grid>
            <Grid item xs={12} md={4} sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="primary" fontWeight={700}>
                3
              </Typography>
              <Typography variant="h6" gutterBottom>
                {t('home.howItWorks.step3.title')}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t('home.howItWorks.step3.description')}
              </Typography>
            </Grid>
          </Grid>
        </Paper>
      </Box>

      {/* CTA Section */}
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Typography variant="h5" gutterBottom>
          {t('home.cta.title')}
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          {t('home.cta.subtitle')}
        </Typography>
        <Button
          variant="contained"
          size="large"
          startIcon={<UploadIcon />}
          onClick={() => navigate('/upload')}
          sx={{ mt: 2 }}
        >
          {t('home.cta.button')}
        </Button>
      </Box>
    </Box>
  );
};

export default HomePage;
