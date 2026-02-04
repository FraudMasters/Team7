import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Container, Typography, Button, Stack, Grid, IconButton, Menu, MenuItem, Dialog, DialogTitle, DialogContent, DialogActions, Paper, Chip } from '@/components/ui';
import { Icon } from '@/components/ui';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../../api/client';

interface Vacancy {
  id: string;
  title: string;
  description: string;
  required_skills: string[];
  min_experience_months?: number;
  industry?: string;
  work_format?: string;
  location?: string;
  salary_min?: number;
  salary_max?: number;
}

export function VacanciesPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedVacancy, setSelectedVacancy] = useState<Vacancy | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  const { data: vacanciesData, isLoading, error } = useQuery({
    queryKey: ['vacancies'],
    queryFn: async () => {
      const response = await apiClient.get<{ vacancies: Vacancy[] }>('/vacancies');
      return response.data;
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/vacancies/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vacancies'] });
      setDeleteDialogOpen(false);
      setSelectedVacancy(null);
    },
  });

  const vacancies = vacanciesData?.vacancies || [];

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, vacancy: Vacancy) => {
    setAnchorEl(event.currentTarget);
    setSelectedVacancy(vacancy);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedVacancy(null);
  };

  const handleEdit = () => {
    if (selectedVacancy) {
      navigate(`/recruiter/vacancies/${selectedVacancy.id}/edit`);
    }
    handleMenuClose();
  };

  const handleDeleteClick = () => {
    setDeleteDialogOpen(true);
    handleMenuClose();
  };

  const handleDeleteConfirm = () => {
    if (selectedVacancy) {
      deleteMutation.mutate(selectedVacancy.id);
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 12 }}>
        Loading vacancies...
      </Box>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 2 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 4 }}>
        <Box>
          <Typography variant="h4" fontWeight={700}>
            Job Postings
          </Typography>
          <Typography variant="body1" color="secondary">
            Manage your open positions
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<Icon name="plus" size={20} />}
          onClick={() => navigate('/recruiter/vacancies/create')}
        >
          Create Vacancy
        </Button>
      </Stack>

      {vacancies.length === 0 ? (
        <Paper sx={{ p: 6, textAlign: 'center' }}>
          <Typography variant="h6" gutterBottom>
            No job postings yet
          </Typography>
          <Typography variant="body2" color="secondary" sx={{ mb: 3 }}>
            Create your first vacancy to start receiving applications
          </Typography>
          <Button
            variant="contained"
            startIcon={<Icon name="plus" size={20} />}
            onClick={() => navigate('/recruiter/vacancies/create')}
          >
            Create Vacancy
          </Button>
        </Paper>
      ) : (
        <Grid container spacing={2}>
          {vacancies.map((vacancy, index) => {
            const visibleSkills = vacancy.required_skills?.slice(0, 3) || [];
            const remainingSkillsCount = Math.max(0, (vacancy.required_skills?.length || 0) - 3);

            return (
              <Grid item xs={12} md={6} lg={4} key={vacancy.id}>
                <Paper
                  sx={{
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    animation: `fadeInUp 0.5s ease-out ${index * 50}ms both`,
                    '@keyframes fadeInUp': {
                      '0%': {
                        opacity: 0,
                        transform: 'translateY(20px)',
                      },
                      '100%': {
                        opacity: 1,
                        transform: 'translateY(0)',
                      },
                    },
                  }}
                >
                <Box sx={{ p: 3, flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
                  <Stack direction="row" justifyContent="space-between" alignItems="flex-start" sx={{ mb: 2 }}>
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="h6" fontWeight={600} gutterBottom>
                        {vacancy.title}
                      </Typography>
                      <Typography variant="body2" color="secondary">
                        {vacancy.location}
                      </Typography>
                    </Box>
                    <IconButton size="small" onClick={(e) => handleMenuOpen(e, vacancy)}>
                      <Icon name="more-vertical" size={20} />
                    </IconButton>
                  </Stack>

                  <Stack direction="row" spacing={1} flexWrap="wrap" gap={1} sx={{ mb: 2 }}>
                    {vacancy.work_format && (
                      <Chip label={vacancy.work_format} size="small" variant="outlined" />
                    )}
                    {vacancy.salary_min && (
                      <Chip label={`$${vacancy.salary_min.toLocaleString()}`} size="small" color="success" variant="outlined" />
                    )}
                  </Stack>

                  <Stack direction="row" spacing={1} flexWrap="wrap" gap={0.5} sx={{ mt: 'auto' }}>
                    {visibleSkills.map((skill) => (
                      <Chip key={skill} label={skill} size="small" variant="outlined" />
                    ))}
                    {remainingSkillsCount > 0 && (
                      <Chip label={`+${remainingSkillsCount}`} size="small" variant="outlined" />
                    )}
                  </Stack>
                </Box>
              </Paper>
              </Grid>
            );
          })}
        </Grid>
      )}

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleEdit}>
          <Icon name="edit" size={16} sx={{ mr: 1 }} />
          Edit
        </MenuItem>
        <MenuItem onClick={handleDeleteClick} sx={{ color: 'error' }}>
          <Icon name="trash-2" size={16} sx={{ mr: 1 }} />
          Delete
        </MenuItem>
      </Menu>

      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete this vacancy?</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete "{selectedVacancy?.title}"? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleDeleteConfirm}
            color="error"
            variant="contained"
            disabled={deleteMutation.isPending}
          >
            {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
