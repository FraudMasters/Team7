import React from 'react';
import {
  Container,
  Typography,
  Box,
} from '@mui/material';
import ModelTrainingDashboard from '@components/ModelTrainingDashboard';

/**
 * Model Training Page (Admin)
 *
 * Admin dashboard for monitoring and managing ML model training pipeline.
 * Displays training metrics, pipeline health, and manual controls.
 */
const ModelTrainingPage: React.FC = () => {
  return (
    <Container maxWidth="xl" sx={{ py: 4 }} className="model-training-dashboard">
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" fontWeight={700} gutterBottom>
          Обучение моделей ML
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Мониторинг и управление автоматическим переобучением моделей
        </Typography>
      </Box>

      {/* Dashboard */}
      <Box>
        <ModelTrainingDashboard />
      </Box>
    </Container>
  );
};

export default ModelTrainingPage;
