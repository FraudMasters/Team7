/**
 * Interview Scheduling Page for Candidates
 *
 * Allows candidates to view their scheduled interviews, reschedule, and
 * manage their interview calendar.
 */

import { useState } from 'react';
import { Container, Box, Button, Typography, Paper, Stack } from '@mui/material';
import {
  Event as EventIcon,
  CalendarMonth as CalendarIcon,
} from '@mui/icons-material';
import { InterviewList } from '../../components/InterviewList';
import { InterviewScheduler } from '../../components/InterviewScheduler';
import { CalendarConnectionManager } from '../../components/CalendarConnectionManager';

export function InterviewSchedulingPage() {
  const [schedulerOpen, setSchedulerOpen] = useState(false);
  const [calendarManagerOpen, setCalendarManagerOpen] = useState(false);

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
              My Interviews
            </Typography>
            <Typography variant="body1" color="text.secondary">
              View and manage your scheduled interviews
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
          candidateId=""
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

export default InterviewSchedulingPage;
