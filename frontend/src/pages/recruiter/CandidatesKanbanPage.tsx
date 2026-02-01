import { useState, useMemo } from 'react';
import { Container, Box, TextField, Typography, Paper, Stack, Grid } from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';
import { KanbanBoard } from '../../components/kanban/KanbanBoard';
import { useCandidates, useCandidateStages, useUpdateCandidateStage } from '../../hooks/useRecruiterData';
import type { DropResult } from '@hello-pangea/dnd';

const DEFAULT_STAGES = ['Applied', 'Screening', 'Interview', 'Offer', 'Hired'];

export function CandidatesKanbanPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const { data: candidatesData } = useCandidates();
  const { data: stagesData } = useCandidateStages();
  const updateStage = useUpdateCandidateStage();

  const stages = stagesData || DEFAULT_STAGES;

  const columns = useMemo(() => {
    const candidates = candidatesData?.candidates || [];
    const filtered = candidates.filter((c) =>
      c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.email.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return stages.map((stage) => ({
      id: stage.toLowerCase().replace(/\s+/g, '-'),
      title: stage,
      candidates: filtered.filter((c) => c.stage === stage || 'Applied'),
    }));
  }, [candidatesData, stages, searchTerm]);

  const handleDragEnd = async (result: DropResult) => {
    if (!result.destination) return;

    const candidateId = result.draggableId as string;
    const newStage = columns[result.destination.droppableId].title;

    await updateStage.mutateAsync({ candidateId, stage: newStage });
  };

  return (
    <Container maxWidth="xl" sx={{ py: 2, height: 'calc(100vh - 100px)', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Candidate Pipeline
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Drag candidates between stages to update their status
        </Typography>
      </Box>

      <TextField
        placeholder="Search candidates..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        InputProps={{
          startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
        }}
        sx={{ mb: 3, maxWidth: 400 }}
      />

      <Box sx={{ flex: 1, overflow: 'hidden' }}>
        <KanbanBoard columns={columns} onDragEnd={handleDragEnd} />
      </Box>
    </Container>
  );
}
