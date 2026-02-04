import React, { useState } from 'react';
import { Typography, Box, Tabs, Tab, Container, useMediaQuery, useTheme } from '@mui/material';
import { useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import AnalysisResults from '@components/AnalysisResults';
import VacancyMatchResults from '@components/VacancyMatchResults';
import { PageTransition } from '../../components/ui/PageTransition';
import { ErrorState } from '../../components/ui/ErrorState';

/**
 * Candidate Detail Page Component
 *
 * Displays comprehensive candidate information including:
 * - Resume analysis with error detection and skill extraction
 * - Grammar and spelling checking results
 * - Experience summary
 * - Vacancy match results with skill highlighting
 * - Best match recommendation
 *
 * Mobile-optimized with responsive layout, scrollable tabs, and touch-friendly interactions
 */
const CandidateDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState(0);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  if (!id) {
    return (
      <PageTransition>
        <Container maxWidth="lg" sx={{ py: { xs: 2, sm: 4 } }}>
          <ErrorState
            title="Candidate Not Found"
            message="No candidate ID provided. Please select a valid candidate from the candidates list."
            onRetry={() => window.history.back()}
          />
        </Container>
      </PageTransition>
    );
  }

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  return (
    <PageTransition>
      <Container
        maxWidth="lg"
        sx={{
          py: { xs: 2, sm: 4 },
          px: { xs: 1, sm: 2 },
          maxWidth: { xs: '100%', sm: 'lg' },
          overflowX: 'hidden'
        }}
      >
        <Box
          sx={{
            mb: { xs: 2, sm: 3 },
            display: 'flex',
            flexDirection: 'column',
            width: '100%'
          }}
        >
          <Typography
            variant={isMobile ? "h5" : "h4"}
            component="h1"
            gutterBottom
            fontWeight={600}
            sx={{
              fontSize: { xs: '1.5rem', sm: '2.125rem' }
            }}
          >
            Candidate Details
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ wordBreak: 'break-word' }}>
            Resume ID: {id}
          </Typography>
        </Box>

        <Box
          sx={{
            borderBottom: 1,
            borderColor: 'divider',
            mb: { xs: 2, sm: 3 },
            width: '100%'
          }}
        >
          <Tabs
            value={activeTab}
            onChange={handleTabChange}
            aria-label="candidate details tabs"
            variant={isMobile ? "fullWidth" : "standard"}
            centered={!isMobile}
            sx={{
              minHeight: { xs: 48, sm: 48 },
              '& .MuiTab-root': {
                minHeight: { xs: 48, sm: 48 },
                minWidth: { xs: 80, sm: 160 },
                fontSize: { xs: '0.875rem', sm: '0.875rem' },
                px: { xs: 1, sm: 2 }
              }
            }}
          >
            <Tab label="Analysis" />
            <Tab label="Vacancy Matches" />
          </Tabs>
        </Box>

        <Box sx={{ width: '100%', overflowX: 'hidden' }}>
          {activeTab === 0 && <AnalysisResults resumeId={id} />}
          {activeTab === 1 && <VacancyMatchResults resumeId={id} />}
        </Box>
      </Container>
    </PageTransition>
  );
};

export default CandidateDetailPage;
export { CandidateDetailPage };
