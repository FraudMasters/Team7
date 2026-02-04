import React, { useState } from 'react';
import { Typography, Box, Tabs, Tab, Container, Button } from '@mui/material';
import { useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Event as EventIcon } from '@mui/icons-material';
import AnalysisResults from '@components/AnalysisResults';
import VacancyMatchResults from '@components/VacancyMatchResults';
import { InterviewScheduler } from '@components/InterviewScheduler';
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
 */
const CandidateDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState(0);
  const [schedulerOpen, setSchedulerOpen] = useState(false);

  if (!id) {
    return (
      <PageTransition>
        <Container maxWidth="lg" sx={{ py: 4 }}>
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
      <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom fontWeight={600}>
          Candidate Details
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Resume ID: {id}
        </Typography>
      </Box>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={handleTabChange} aria-label="candidate details tabs">
          <Tab label="Analysis" />
          <Tab label="Vacancy Matches" />
          <Tab label="Schedule Interview" />
        </Tabs>
      </Box>

      {activeTab === 0 && <AnalysisResults resumeId={id} />}
      {activeTab === 1 && <VacancyMatchResults resumeId={id} />}
      {activeTab === 2 && (
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 8 }}>
          <Typography variant="h6" gutterBottom>
            Schedule an Interview
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Select date, time, and interviewers to schedule an interview for this candidate
          </Typography>
          <Button
            variant="contained"
            startIcon={<EventIcon />}
            onClick={() => setSchedulerOpen(true)}
            size="large"
          >
            Open Interview Scheduler
          </Button>
          {schedulerOpen && (
            <InterviewScheduler
              candidateId={id}
              onCancel={() => setSchedulerOpen(false)}
              onSuccess={() => setSchedulerOpen(false)}
            />
          )}
        </Box>
      )}
    </Container>
    </PageTransition>
  );
};

export default CandidateDetailPage;
export { CandidateDetailPage };
