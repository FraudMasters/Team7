import React from 'react';
import { Typography, Box } from '@mui/material';
import { AutoAwesome as AutoAwesomeIcon } from '@mui/icons-material';
import SmartVacancyWizard from '@/components/SmartVacancyWizard';

const CreateVacancy: React.FC = () => {
  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
          <AutoAwesomeIcon color="primary" sx={{ fontSize: 32 }} />
          <Typography variant="h4" component="h1" fontWeight={600}>
            Умный помощник создания вакансий
          </Typography>
        </Box>
        <Typography variant="body1" color="text.secondary" paragraph>
          Введите позицию и мы предложим готовые пресеты навыков и автодополнение
        </Typography>
      </Box>

      <SmartVacancyWizard />
    </Box>
  );
};

export default CreateVacancy;
