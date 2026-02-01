import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Stack,
  CircularProgress,
  Alert,
  Divider,
  Tooltip,
} from '@mui/material';
import {
  CheckCircle as CheckIcon,
  Psychology as AIIcon,
  Search as SearchIcon,
  AutoFixHigh as MagicIcon,
  Translate as SynonymIcon,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

export interface SkillMatchDetail {
  skill: string;
  confidence: number;
  match_type: 'direct' | 'synonym' | 'fuzzy' | 'context' | 'compound' | 'language_hierarchy';
  matched_as?: string;
  locations?: Array<{
    text: string;
    start: number;
    end: number;
    context: string;
  }>;
}

interface SkillDetailsWithConfidenceProps {
  skills: SkillMatchDetail[];
  loading?: boolean;
  error?: string | null;
  title?: string;
  maxDisplay?: number;
}

const StyledCard = styled(Card)(({ theme }) => ({
  marginBottom: theme.spacing(2),
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
}));

const ConfidenceBar = styled('div')<{ confidence: number }>(({ theme, confidence }) => ({
  height: 4,
  borderRadius: 2,
  backgroundColor: theme.palette.grey[200],
  position: 'relative',
  overflow: 'hidden',
  marginTop: theme.spacing(0.5),
  '&::after': {
    content: '""',
    position: 'absolute',
    left: 0,
    top: 0,
    bottom: 0,
    width: `${confidence * 100}%`,
    backgroundColor:
      confidence >= 0.9
        ? theme.palette.success.main
        : confidence >= 0.7
        ? theme.palette.primary.main
        : confidence >= 0.5
        ? theme.palette.warning.main
        : theme.palette.error.main,
    transition: 'width 0.3s ease',
  },
}));

const getMatchTypeConfig = (matchType: string) => {
  switch (matchType) {
    case 'direct':
      return {
        label: 'Direct',
        icon: <CheckIcon fontSize="small" />,
        color: 'success' as const,
        bgColor: 'success.light' as const,
        description: 'Exact match found in resume',
      };
    case 'synonym':
      return {
        label: 'Synonym',
        icon: <SynonymIcon fontSize="small" />,
        color: 'info' as const,
        bgColor: 'info.light' as const,
        description: 'Matched through known synonyms',
      };
    case 'fuzzy':
      return {
        label: 'Fuzzy',
        icon: <SearchIcon fontSize="small" />,
        color: 'warning' as const,
        bgColor: 'warning.light' as const,
        description: 'Partial match (typo or variation)',
      };
    case 'context':
      return {
        label: 'Context',
        icon: <AIIcon fontSize="small" />,
        color: 'secondary' as const,
        bgColor: 'secondary.light' as const,
        description: 'Matched based on domain context',
      };
    case 'compound':
      return {
        label: 'Compound',
        icon: <MagicIcon fontSize="small" />,
        color: 'primary' as const,
        bgColor: 'primary.light' as const,
        description: 'Compound skill match',
      };
    case 'language_hierarchy':
      return {
        label: 'Hierarchy',
        icon: <AIIcon fontSize="small" />,
        color: 'info' as const,
        bgColor: 'info.light' as const,
        description: 'Matched through language hierarchy',
      };
    default:
      return {
        label: 'Unknown',
        icon: <CheckIcon fontSize="small" />,
        color: 'default' as const,
        bgColor: 'grey.100' as const,
        description: 'Unknown match type',
      };
  }
};

const SkillDetailsWithConfidence: React.FC<SkillDetailsWithConfidenceProps> = ({
  skills,
  loading = false,
  error = null,
  title = 'Matched Skills Details',
  maxDisplay = 20,
}) => {
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
        <Typography variant="body1" sx={{ ml: 2 }}>
          Loading skill details...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!skills || skills.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <CheckIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
        <Typography variant="h6" color="text.secondary">
          No matched skills
        </Typography>
        <Typography variant="body2" color="text.secondary">
          No skills were matched for this position
        </Typography>
      </Box>
    );
  }

  const displaySkills = skills.slice(0, maxDisplay);
  const hasMore = skills.length > maxDisplay;

  return (
    <StyledCard>
      <CardContent>
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            mb: 2,
          }}
        >
          <Typography variant="h6" fontWeight={600}>
            {title}
          </Typography>
          <Chip
            label={`${skills.length} skills`}
            size="small"
            color="primary"
            variant="outlined"
          />
        </Box>

        <Divider sx={{ mb: 2 }} />

        <Stack spacing={2}>
          {displaySkills.map((skillDetail, index) => {
            const matchConfig = getMatchTypeConfig(skillDetail.match_type);
            const confidencePercent = Math.round(skillDetail.confidence * 100);

            return (
              <Box
                key={`${skillDetail.skill}-${index}`}
                sx={{
                  p: 1.5,
                  borderRadius: 1,
                  backgroundColor: 'grey.50',
                  transition: 'background-color 0.2s',
                  '&:hover': {
                    backgroundColor: 'grey.100',
                  },
                }}
              >
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    mb: 1,
                  }}
                >
                  <Box sx={{ flex: 1 }}>
                    <Typography
                      variant="subtitle2"
                      fontWeight={600}
                      sx={{ mb: 0.5 }}
                    >
                      {skillDetail.skill}
                      {skillDetail.matched_as &&
                        skillDetail.matched_as !== skillDetail.skill && (
                          <Typography
                            component="span"
                            variant="caption"
                            color="text.secondary"
                            sx={{ ml: 1, fontWeight: 400 }}
                          >
                            (matched as "{skillDetail.matched_as}")
                          </Typography>
                        )}
                    </Typography>

                    <Stack direction="row" spacing={0.5} alignItems="center">
                      <Tooltip title={matchConfig.description} arrow>
                        <Chip
                          icon={matchConfig.icon}
                          label={matchConfig.label}
                          size="small"
                          color={matchConfig.color}
                          variant="outlined"
                          sx={{ fontSize: '0.7rem', height: 20 }}
                        />
                      </Tooltip>

                      <Chip
                        label={`${confidencePercent}%`}
                        size="small"
                        sx={{
                          fontSize: '0.7rem',
                          height: 20,
                          fontWeight: 600,
                          backgroundColor:
                            skillDetail.confidence >= 0.9
                              ? 'success.light'
                              : skillDetail.confidence >= 0.7
                              ? 'primary.light'
                              : skillDetail.confidence >= 0.5
                              ? 'warning.light'
                              : 'error.light',
                        }}
                      />
                    </Stack>
                  </Box>
                </Box>

                <ConfidenceBar confidence={skillDetail.confidence} />

                {skillDetail.locations && skillDetail.locations.length > 0 && (
                  <Box sx={{ mt: 1 }}>
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      sx={{ display: 'block', mb: 0.5, fontWeight: 500 }}
                    >
                      Found in resume:
                    </Typography>
                    {skillDetail.locations.slice(0, 2).map((location, idx) => (
                      <Box
                        key={idx}
                        sx={{
                          p: 0.75,
                          mt: idx > 0 ? 0.5 : 0,
                          backgroundColor: 'background.paper',
                          borderRadius: 0.5,
                          border: '1px solid',
                          borderColor: 'divider',
                        }}
                      >
                        <Typography
                          variant="caption"
                          sx={{
                            fontFamily: 'monospace',
                            fontSize: '0.65rem',
                            color: 'text.primary',
                            display: 'block',
                            lineHeight: 1.4,
                          }}
                        >
                          {location.context}
                        </Typography>
                      </Box>
                    ))}
                    {skillDetail.locations.length > 2 && (
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        sx={{ display: 'block', mt: 0.5, fontStyle: 'italic' }}
                      >
                        +{skillDetail.locations.length - 2} more locations
                      </Typography>
                    )}
                  </Box>
                )}
              </Box>
            );
          })}
        </Stack>

        {hasMore && (
          <Box sx={{ mt: 2, textAlign: 'center' }}>
            <Typography variant="caption" color="text.secondary">
              Showing {maxDisplay} of {skills.length} matched skills
            </Typography>
          </Box>
        )}
      </CardContent>
    </StyledCard>
  );
};

export default SkillDetailsWithConfidence;
