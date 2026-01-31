import React, { useState, useEffect } from 'react';
import {
  Typography,
  Box,
  Container,
  Paper,
  Grid,
  Card,
  CardContent,
  CardActions,
  Chip,
  CircularProgress,
  TextField,
  InputAdornment,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
} from '@mui/material';
import {
  Work as WorkIcon,
  Search as SearchIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import axios from 'axios';

interface Resume {
  id: string;
  filename: string;
  status: string;
  created_at: string;
  language?: string;
  skills: string[];
}

/**
 * Resume Database Page (Recruiter Module)
 *
 * Allows recruiters to browse the resume database.
 * Shows candidate profiles with their skills and experience.
 */
const ResumeDatabasePage: React.FC = () => {
  const { t } = useTranslation();
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [filteredResumes, setFilteredResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [resumeToDelete, setResumeToDelete] = useState<string | null>(null);

  const fetchResumes = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/resumes/?limit=100');
      // Map technical_skills to skills for compatibility
      const resumesWithSkills = response.data.map((r: any) => ({
        ...r,
        skills: r.technical_skills || [],
      }));
      setResumes(resumesWithSkills);
      setFilteredResumes(resumesWithSkills);
    } catch (error) {
      console.error('Error fetching resumes:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResumes();
  }, []);

  // Filter resumes based on search query
  useEffect(() => {
    if (!searchQuery) {
      setFilteredResumes(resumes);
      return;
    }

    const query = searchQuery.toLowerCase();
    const filtered = resumes.filter((resume) =>
      resume.skills?.some((skill) => skill.toLowerCase().includes(query)) ||
      resume.filename?.toLowerCase().includes(query)
    );
    setFilteredResumes(filtered);
  }, [searchQuery, resumes]);

  const getTitleFromFilename = (filename: string) => {
    // Extract CV number from filename like "CV_1.docx"
    const match = filename.match(/CV_(\d+)\.docx/);
    return match ? t('resumeDatabase.candidate', { number: match[1] }) : filename;
  };

  const handleDeleteClick = (id: string) => {
    setResumeToDelete(id);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!resumeToDelete) return;

    try {
      await axios.delete(`/api/resumes/${resumeToDelete}`);
      // Remove from list
      setResumes(resumes.filter((r) => r.id !== resumeToDelete));
      setFilteredResumes(filteredResumes.filter((r) => r.id !== resumeToDelete));
      setDeleteDialogOpen(false);
      setResumeToDelete(null);
    } catch (error) {
      console.error('Error deleting resume:', error);
      alert('Failed to delete resume');
    }
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom fontWeight={600}>
          {t('resumeDatabase.title')}
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          {t('resumeDatabase.subtitle', { count: resumes.length })}
        </Typography>

        {/* Search Bar */}
        <Paper sx={{ p: 2, mb: 4 }}>
          <TextField
            fullWidth
            placeholder={t('resumeDatabase.searchPlaceholder')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />
        </Paper>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : filteredResumes.length === 0 ? (
          <Paper sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="body1" color="text.secondary">
              {searchQuery ? t('resumeDatabase.noResumesSearch') : t('resumeDatabase.noResumes')}
            </Typography>
          </Paper>
        ) : (
          <Grid container spacing={3}>
            {filteredResumes.map((resume) => (
              <Grid item xs={12} md={6} key={resume.id}>
                <Card
                  sx={{
                    height: '100%',
                    cursor: 'pointer',
                    transition: 'transform 0.2s, box-shadow 0.2s',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: 4,
                    },
                  }}
                  onClick={() => (window.location.href = `/results/${resume.id}`)}
                >
                  <CardContent sx={{ pb: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <WorkIcon sx={{ mr: 1, color: 'primary.main' }} />
                      <Typography variant="h6" sx={{ flex: 1 }}>
                        {getTitleFromFilename(resume.filename)}
                      </Typography>
                      <Chip
                        label={resume.status}
                        size="small"
                        color={resume.status === 'COMPLETED' ? 'success' : 'default'}
                      />
                    </Box>

                    <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                      ID: {resume.id.slice(0, 8)}...
                    </Typography>

                    {resume.skills && resume.skills.length > 0 ? (
                      <Box sx={{ mt: 2 }}>
                        {resume.skills.slice(0, 8).map((skill) => (
                          <Chip
                            key={skill}
                            label={skill}
                            size="small"
                            variant="outlined"
                            sx={{ mr: 0.5, mb: 0.5, fontSize: '0.75rem' }}
                          />
                        ))}
                        {resume.skills.length > 8 && (
                          <Chip
                            label={t('resumeDatabase.moreSkills', { count: resume.skills.length - 8 })}
                            size="small"
                            variant="outlined"
                            sx={{ fontSize: '0.75rem' }}
                          />
                        )}
                      </Box>
                    ) : (
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 1, fontStyle: 'italic' }}>
                        {t('resumeDatabase.noSkills')}
                      </Typography>
                    )}
                  </CardContent>
                  <CardActions sx={{ justifyContent: 'flex-end', px: 2, pb: 2 }}>
                    <IconButton
                      size="small"
                      color="error"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteClick(resume.id);
                      }}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}

        {/* Delete Confirmation Dialog */}
        <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
          <DialogTitle>{t('resumeDatabase.deleteDialog.title')}</DialogTitle>
          <DialogContent>
            <Typography>
              {t('resumeDatabase.deleteDialog.message')}
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDeleteDialogOpen(false)}>{t('common.cancel')}</Button>
            <Button onClick={handleDeleteConfirm} color="error" variant="contained">
              {t('common.delete')}
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </Container>
  );
};

export default ResumeDatabasePage;
