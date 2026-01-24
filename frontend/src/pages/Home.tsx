import React from 'react';
import { useNavigate } from 'react-router-dom';
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

  const features = [
    {
      icon: <AIIcon fontSize="large" color="primary" />,
      title: 'AI-Powered Analysis',
      description: 'Advanced ML/NLP techniques for intelligent resume parsing and error detection',
    },
    {
      icon: <SuccessIcon fontSize="large" color="success" />,
      title: 'Error Detection',
      description: 'Identify grammar issues, missing information, and structural problems instantly',
    },
    {
      icon: <CompareIcon fontSize="large" color="secondary" />,
      title: 'Job Matching',
      description: 'Compare resumes against job vacancies with skill highlighting and experience verification',
    },
    {
      icon: <SpeedIcon fontSize="large" color="info" />,
      title: 'Fast Processing',
      description: 'Get comprehensive analysis results in seconds with our optimized pipeline',
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
          Transform Your Recruitment Process
        </Typography>
        <Typography variant="h5" color="text.secondary" paragraph sx={{ mb: 4 }}>
          AI-powered resume analysis platform with intelligent job matching
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
          <Button
            variant="contained"
            size="large"
            startIcon={<UploadIcon />}
            onClick={() => navigate('/upload')}
            sx={{ px: 4, py: 1.5, fontSize: '1.1rem' }}
          >
            Upload Resume
          </Button>
          <Button
            variant="outlined"
            size="large"
            startIcon={<AnalysisIcon />}
            onClick={() => navigate('/results')}
            sx={{ px: 4, py: 1.5, fontSize: '1.1rem' }}
          >
            View Sample Analysis
          </Button>
        </Box>
      </Box>

      {/* Features Grid */}
      <Box sx={{ mb: 6 }}>
        <Typography variant="h4" component="h2" gutterBottom align="center" sx={{ mb: 4 }}>
          Powerful Features
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
          How It Works
        </Typography>
        <Paper elevation={2} sx={{ p: 4 }}>
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} md={4} sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="primary" fontWeight={700}>
                1
              </Typography>
              <Typography variant="h6" gutterBottom>
                Upload Resume
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Upload PDF or DOCX resume files through our intuitive interface
              </Typography>
            </Grid>
            <Grid item xs={12} md={4} sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="primary" fontWeight={700}>
                2
              </Typography>
              <Typography variant="h6" gutterBottom>
                AI Analysis
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Our AI extracts skills, detects errors, and calculates experience
              </Typography>
            </Grid>
            <Grid item xs={12} md={4} sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="primary" fontWeight={700}>
                3
              </Typography>
              <Typography variant="h6" gutterBottom>
                Get Results
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Receive detailed analysis with recommendations and job matching
              </Typography>
            </Grid>
          </Grid>
        </Paper>
      </Box>

      {/* CTA Section */}
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Typography variant="h5" gutterBottom>
          Ready to analyze your first resume?
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          Get started in seconds with our easy-to-use interface
        </Typography>
        <Button
          variant="contained"
          size="large"
          startIcon={<UploadIcon />}
          onClick={() => navigate('/upload')}
          sx={{ mt: 2 }}
        >
          Get Started
        </Button>
      </Box>
    </Box>
  );
};

export default HomePage;
