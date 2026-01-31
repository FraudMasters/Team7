import React from 'react';
import { Typography, Box, Container, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from '@mui/material';

/**
 * Job Applications Page
 *
 * Displays all job applications submitted by the current user.
 * Shows application status, vacancy details, and match percentage.
 */
const ApplicationsPage: React.FC = () => {
  // Placeholder data - replace with actual API calls
  const applications = [
    {
      id: '1',
      vacancyTitle: 'React Developer',
      company: 'Tech Corp',
      status: 'Pending',
      matchPercentage: 85,
      appliedDate: '2025-01-26',
    },
  ];

  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom fontWeight={600}>
          My Applications
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          Track your job applications and their status.
        </Typography>

        {applications.length === 0 ? (
          <Paper sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="body1" color="text.secondary">
              You haven't applied to any vacancies yet.
            </Typography>
          </Paper>
        ) : (
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Vacancy</TableCell>
                  <TableCell>Company</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Match</TableCell>
                  <TableCell>Applied Date</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {applications.map((app) => (
                  <TableRow key={app.id}>
                    <TableCell>{app.vacancyTitle}</TableCell>
                    <TableCell>{app.company}</TableCell>
                    <TableCell>{app.status}</TableCell>
                    <TableCell>{app.matchPercentage}%</TableCell>
                    <TableCell>{app.appliedDate}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Box>
    </Container>
  );
};

export default ApplicationsPage;
