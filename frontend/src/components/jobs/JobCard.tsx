import React from 'react';
import { Link } from 'react-router-dom';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Stack,
  Chip,
  IconButton,
} from '@mui/material';
import {
  LocationOn,
  WorkOutline,
  BookmarkBorder,
  Bookmark,
} from '@mui/icons-material';
import type { JobVacancy } from '../../hooks/useJobs';

interface JobCardProps {
  job: JobVacancy;
  saved?: boolean;
  onSave?: () => void;
}

export function JobCard({ job, saved = false, onSave }: JobCardProps) {
  const maxSkillsToShow = 4;
  const visibleSkills = job.required_skills.slice(0, maxSkillsToShow);
  const remainingSkillsCount = Math.max(0, job.required_skills.length - maxSkillsToShow);

  const handleBookmarkClick = (e: React.MouseEvent) => {
    e.preventDefault();
    onSave?.();
  };

  return (
    <Card
      component={Link}
      to={`/jobs/${job.id}`}
      sx={{
        textDecoration: 'none',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        transition: 'transform 0.2s ease-out, box-shadow 0.2s ease-out',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
        },
      }}
    >
      <CardContent sx={{ flexGrow: 1, p: 3 }}>
        {/* Header with title and bookmark */}
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start" sx={{ mb: 2 }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" fontWeight={600} color="text.primary" gutterBottom>
              {job.title}
            </Typography>
            {job.location && (
              <Stack direction="row" spacing={1} alignItems="center" color="text.secondary">
                <LocationOn sx={{ fontSize: 16 }} />
                <Typography variant="body2">{job.location}</Typography>
              </Stack>
            )}
          </Box>
          <IconButton
            size="small"
            onClick={handleBookmarkClick}
            sx={{ ml: 1 }}
            aria-label={saved ? 'Remove from saved' : 'Save job'}
          >
            {saved ? <Bookmark color="primary" /> : <BookmarkBorder />}
          </IconButton>
        </Stack>

        {/* Description truncated to 2 lines */}
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            mb: 2,
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
          }}
        >
          {job.description}
        </Typography>

        {/* Work format and experience */}
        <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 2 }} color="text.secondary">
          <WorkOutline sx={{ fontSize: 16 }} />
          <Typography variant="body2">
            {job.min_experience_months > 0 && `${Math.floor(job.min_experience_months / 12)}+ years`}
            {job.work_format && ` • ${job.work_format}`}
          </Typography>
        </Stack>

        {/* Skills chips */}
        <Stack direction="row" spacing={1} flexWrap="wrap" gap={0.5}>
          {visibleSkills.map((skill) => (
            <Chip
              key={skill}
              label={skill}
              size="small"
              variant="outlined"
              sx={{
                borderRadius: 1,
                fontSize: '0.75rem',
                height: 24,
              }}
            />
          ))}
          {remainingSkillsCount > 0 && (
            <Chip
              label={`+${remainingSkillsCount}`}
              size="small"
              variant="outlined"
              sx={{ borderRadius: 1, fontSize: '0.75rem', height: 24 }}
            />
          )}
        </Stack>
      </CardContent>
    </Card>
  );
}
