import { Container, Typography, Box, Paper } from '@mui/material';

export function VacancyFormPage() {
  return (
    <Container maxWidth="xl" sx={{ py: 2 }}>
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Create/Edit Vacancy
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Vacancy form coming soon...
        </Typography>
      </Paper>
    </Container>
  );
}
