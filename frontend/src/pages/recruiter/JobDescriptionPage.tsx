import React from 'react';
import { Container } from '@mui/material';
import JobDescriptionGenerator from '../../components/JobDescriptionGenerator';

/**
 * Страница генерации описаний вакансий
 *
 * Предоставляет интерфейс для AI-генерации описаний вакансий на основе
 * введенных параметров (должность, навыки, опыт и т.д.).
 */
export function JobDescriptionPage() {
  return (
    <Container maxWidth="xl" sx={{ py: 2 }}>
      <JobDescriptionGenerator />
    </Container>
  );
}

export default JobDescriptionPage;
