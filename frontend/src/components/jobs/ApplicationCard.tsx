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
} from '@/components/ui';
import { Icon } from '@/components/ui';

export interface JobApplication {
  id: string;
  vacancy_id: string;
  title: string;
  description?: string;
  location?: string;
  work_format?: 'remote' | 'office' | 'hybrid';
  min_experience_months?: number;
  required_skills: string[];
  status: string;
  stage_name?: string;
  applied_at: string;
  match_score?: number;
}

interface ApplicationCardProps {
  application: JobApplication;
  saved?: boolean;
  onSave?: () => void;
}

export function ApplicationCard({ application, saved = false, onSave }: ApplicationCardProps) {
  const maxSkillsToShow = 4;
  const visibleSkills = application.required_skills.slice(0, maxSkillsToShow);
  const remainingSkillsCount = Math.max(0, application.required_skills.length - maxSkillsToShow);

  const handleBookmarkClick = (e: React.MouseEvent) => {
    e.preventDefault();
    onSave?.();
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    return date.toLocaleDateString();
  };

  return (
    <Card
      as={Link}
      to={`/jobs/${application.vacancy_id}`}
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
      <CardContent sx={{ flexGrow: 1, padding: 3 }}>
        {/* Header with title, status and bookmark */}
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start" sx={{ mb: 2 }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" fontWeight={600} color="primary" gutterBottom>
              {application.title}
            </Typography>
            <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 0.5 }}>
              {application.location && (
                <Stack direction="row" spacing={0.5} alignItems="center" color="secondary">
                  <Icon name="map-pin" size={16} />
                  <Typography variant="body2">{application.location}</Typography>
                </Stack>
              )}
            </Stack>
            <Stack direction="row" spacing={1} alignItems="center" color="secondary">
              <Icon name="clock" size={16} />
              <Typography variant="body2">Applied {formatDate(application.applied_at)}</Typography>
            </Stack>
          </Box>
          <IconButton
            size="small"
            onClick={handleBookmarkClick}
            sx={{ ml: 1 }}
            aria-label={saved ? 'Remove from saved' : 'Save job'}
          >
            <Icon name={saved ? 'bookmark' : 'bookmark'} size={20} color={saved ? 'primary' : 'inherit'} filled={saved} />
          </IconButton>
        </Stack>

        {/* Status chip */}
        <Box sx={{ mb: 2 }}>
          <Chip
            label={application.stage_name || application.status}
            size="small"
            sx={{
              borderRadius: 1,
              fontSize: '0.75rem',
              height: 24,
              textTransform: 'capitalize',
            }}
          />
          {application.match_score !== undefined && (
            <Chip
              label={`${Math.round(application.match_score)}% match`}
              size="small"
              color="primary"
              variant="outlined"
              sx={{
                borderRadius: 1,
                fontSize: '0.75rem',
                height: 24,
                ml: 1,
              }}
            />
          )}
        </Box>

        {/* Description truncated to 2 lines */}
        {application.description && (
          <Typography
            variant="body2"
            color="secondary"
            sx={{
              mb: 2,
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
            }}
          >
            {application.description}
          </Typography>
        )}

        {/* Work format and experience */}
        {(application.work_format || application.min_experience_months) && (
          <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 2 }} color="secondary">
            <Icon name="briefcase" size={16} />
            <Typography variant="body2">
              {application.min_experience_months && application.min_experience_months > 0 && `${Math.floor(application.min_experience_months / 12)}+ years`}
              {application.work_format && ` • ${application.work_format}`}
            </Typography>
          </Stack>
        )}

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
