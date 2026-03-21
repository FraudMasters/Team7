import { Container, Box, Typography } from '@mui/material';
import ReportScheduler from '../../components/ReportScheduler';

/**
 * Report Schedule Page
 *
 * Provides interface for managing scheduled report generation and delivery.
 * Displays the ReportScheduler component which allows users to:
 * - View existing scheduled reports
 * - Create new scheduled reports with flexible timing options
 * - Edit existing schedules
 * - Configure delivery settings (format, email content)
 * - Manage recipient lists
 * - Enable/disable schedules
 */
export function ReportSchedulePage() {
  return (
    <Container maxWidth="xl" sx={{ py: 2 }}>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700}>
          Report Schedules
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Automate report generation and delivery on a recurring schedule.
        </Typography>
      </Box>

      {/* Report Scheduler Component */}
      <ReportScheduler />
    </Container>
  );
}

export default ReportSchedulePage;
