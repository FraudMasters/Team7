import React from 'react';
import { Typography, Box } from '@/components/ui';
import { Icon } from '@/components/ui';
import SmartVacancyWizard from '../components/SmartVacancyWizard';

const CreateVacancy: React.FC = () => {
  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
          <Icon name="sparkles" size={32} color="primary" />
          <Typography variant="h4" as="h1" fontWeight={600}>
            Умный помощник создания вакансий
          </Typography>
        </Box>
        <Typography variant="body1" color="secondary" paragraph>
          Введите позицию и мы предложим готовые пресеты навыков и автодополнение
        </Typography>
      </Box>

      <SmartVacancyWizard />
    </Box>
  );
};

export default CreateVacancy;
