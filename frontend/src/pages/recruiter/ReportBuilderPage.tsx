import React from 'react';
import { Container, Typography, Box, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { ArrowBack as BackIcon } from '@mui/icons-material';
import ReportBuilder from '@components/analytics/ReportBuilder';

/**
 * Report Builder Page
 *
 * Dedicated page for building custom analytics reports.
 * Provides a standalone interface for the ReportBuilder component.
 */
const ReportBuilderPage: React.FC = () => {
  const navigate = useNavigate();

  const handleBack = () => {
    navigate('/recruiter/analytics');
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <Button
            variant="outlined"
            startIcon={<BackIcon />}
            onClick={handleBack}
            size="small"
          >
            Back to Analytics
          </Button>
        </Box>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Report Builder
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Create custom analytics reports with selected metrics and filters
        </Typography>
      </Box>

      {/* Report Builder Component */}
      <ReportBuilder
        onReportChange={(report) => {
          // Report configuration saved
        }}
      />
    </Container>
  );
};

export default ReportBuilderPage;
