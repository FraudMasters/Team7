import { Container, Box, Typography } from '@mui/material';
import ReportGenerator from '../../components/ReportGenerator';

/**
 * Reports Page
 *
 * Provides interface for creating and managing custom reports.
 * Displays the ReportGenerator component which allows users to:
 * - Select report templates
 * - Configure report parameters
 * - Generate reports in various formats (PDF, Excel, CSV)
 * - Save report configurations
 */
export function ReportsPage() {
  return (
    <Container maxWidth="xl" sx={{ py: 2 }}>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700}>
          Reports
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Generate professional reports for candidates, pipelines, and compliance.
        </Typography>
      </Box>

      {/* Report Generator Component */}
      <ReportGenerator />
    </Container>
  );
}

export default ReportsPage;
