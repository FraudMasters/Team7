import { useState } from 'react';
import { Container, Box, Button, Typography, Paper, Stack, Grid2 } from '@mui/material';
import {
  Event as EventIcon,
  Add as AddIcon,
  CalendarMonth as CalendarIcon,
} from '@mui/icons-material';
import { InterviewList } from '../components/InterviewList';
import { InterviewScheduler } from '../components/InterviewScheduler';
import { CalendarConnectionManager } from '../components/CalendarConnectionManager';

export function InterviewSchedulePage() {
  const [schedulerOpen, setSchedulerOpen] = useState(false);
  const [calendarManagerOpen, setCalendarManagerOpen] = useState(false);
  const [selectedCandidateId, setSelectedCandidateId] = useState<string>();
  const [selectedVacancyId, setSelectedVacancyId] = useState<string>();

  const handleScheduleInterview = () => {
    setSelectedCandidateId(undefined);
    setSelectedVacancyId(undefined);
    setSchedulerOpen(true);
  };

  const handleScheduleSuccess = () => {
    setSchedulerOpen(false);
  };

  const handleScheduleCancel = () => {
    setSchedulerOpen(false);
  };

  return (
    <Container maxWidth="xl" sx={{ py: 2, height: 'calc(100vh - 100px)', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ mb: 3 }}>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography variant="h4" fontWeight={700} gutterBottom>
              Interview Schedule
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Manage interviews, check availability, and sync with calendar
            </Typography>
          </Box>
          <Stack direction="row" spacing={2}>
            <Button
              variant="outlined"
              startIcon={<CalendarIcon />}
              onClick={() => setCalendarManagerOpen(true)}
            >
              Calendar Settings
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleScheduleInterview}
            >
              Schedule Interview
            </Button>
          </Stack>
        </Stack>
      </Box>

      <Paper sx={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ flex: 1, overflow: 'auto' }}>
          <InterviewList />
        </Box>
      </Paper>

      {schedulerOpen && (
        <InterviewScheduler
          candidateId={selectedCandidateId || ''}
          vacancyId={selectedVacancyId}
          onSuccess={handleScheduleSuccess}
          onCancel={handleScheduleCancel}
        />
      )}

      <CalendarConnectionManager
        open={calendarManagerOpen}
        onClose={() => setCalendarManagerOpen(false)}
      />
    </Container>
  );
}
