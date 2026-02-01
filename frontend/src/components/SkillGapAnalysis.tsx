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
  Collapse,
  IconButton,
} from '@mui/material';
import {
  Cancel as MissingIcon,
  Lightbulb as SuggestionIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Psychology as AIIcon,
  Translate as SynonymIcon,
  Category as CategoryIcon,
  Search as FuzzyIcon,
  Link as RelatedIcon,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

export interface SkillSuggestion {
  skill: string;
  confidence: number;
  reason: 'synonym' | 'same_category' | 'related' | 'fuzzy_match' | string;
}

export interface MissingSkillWithSuggestions {
  skill: string;
  suggestions: SkillSuggestion[];
}

interface SkillGapAnalysisProps {
  missingSkills: MissingSkillWithSuggestions[];
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

const SuggestionBar = styled('div')<{ confidence: number }>(({ theme, confidence }) => ({
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
      confidence >= 0.8
        ? theme.palette.success.main
        : confidence >= 0.65
        ? theme.palette.info.main
        : confidence >= 0.5
        ? theme.palette.warning.main
        : theme.palette.error.main,
    transition: 'width 0.3s ease',
  },
}));

const getSuggestionReasonConfig = (reason: string) => {
  switch (reason) {
    case 'synonym':
      return {
        label: 'Synonym',
        icon: <SynonymIcon fontSize="small" />,
        color: 'success' as const,
        bgColor: 'success.light' as const,
        description: 'Known synonym or equivalent term',
      };
    case 'same_category':
      return {
        label: 'Category',
        icon: <CategoryIcon fontSize="small" />,
        color: 'info' as const,
        bgColor: 'info.light' as const,
        description: 'From the same skill category',
      };
    case 'related':
      return {
        label: 'Related',
        icon: <RelatedIcon fontSize="small" />,
        color: 'secondary' as const,
        bgColor: 'secondary.light' as const,
        description: 'Commonly used together',
      };
    case 'fuzzy_match':
      return {
        label: 'Similar',
        icon: <FuzzyIcon fontSize="small" />,
        color: 'warning' as const,
        bgColor: 'warning.light' as const,
        description: 'Similar name or variation',
      };
    default:
      return {
        label: 'Suggestion',
        icon: <AIIcon fontSize="small" />,
        color: 'default' as const,
        bgColor: 'grey.100' as const,
        description: 'Suggested alternative',
      };
  }
};

const SkillGapAnalysis: React.FC<SkillGapAnalysisProps> = ({
  missingSkills,
  loading = false,
  error = null,
  title = 'Skill Gap Analysis',
  maxDisplay = 20,
}) => {
  const [expandedSkills, setExpandedSkills] = React.useState<Set<string>>(new Set());

  const toggleExpanded = (skill: string) => {
    setExpandedSkills((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(skill)) {
        newSet.delete(skill);
      } else {
        newSet.add(skill);
      }
      return newSet;
    });
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
        <Typography variant="body1" sx={{ ml: 2 }}>
          Analyzing skill gaps...
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

  if (!missingSkills || missingSkills.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <SuggestionIcon sx={{ fontSize: 48, color: 'success.main', mb: 2 }} />
        <Typography variant="h6" color="text.secondary">
          No Missing Skills
        </Typography>
        <Typography variant="body2" color="text.secondary">
          All required skills are covered in the resume
        </Typography>
      </Box>
    );
  }

  const displaySkills = missingSkills.slice(0, maxDisplay);
  const hasMore = missingSkills.length > maxDisplay;

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
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <MissingIcon sx={{ color: 'warning.main' }} />
            <Typography variant="h6" fontWeight={600}>
              {title}
            </Typography>
          </Box>
          <Chip
            label={`${missingSkills.length} missing`}
            size="small"
            color="warning"
            variant="outlined"
          />
        </Box>

        <Divider sx={{ mb: 2 }} />

        <Stack spacing={2}>
          {displaySkills.map((missingSkill, index) => {
            const isExpanded = expandedSkills.has(missingSkill.skill);
            const hasSuggestions = missingSkill.suggestions && missingSkill.suggestions.length > 0;

            return (
              <Box
                key={`${missingSkill.skill}-${index}`}
                sx={{
                  p: 1.5,
                  borderRadius: 1,
                  backgroundColor: 'warning.50',
                  border: '1px solid',
                  borderColor: 'warning.200',
                  transition: 'background-color 0.2s',
                  '&:hover': {
                    backgroundColor: 'warning.100',
                  },
                }}
              >
                {/* Missing Skill Header */}
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <Box sx={{ flex: 1 }}>
                    <Typography
                      variant="subtitle2"
                      fontWeight={600}
                      sx={{ mb: 0.5 }}
                      color="warning.dark"
                    >
                      {missingSkill.skill}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {hasSuggestions
                        ? `${missingSkill.suggestions.length} suggestion${missingSkill.suggestions.length > 1 ? 's' : ''} available`
                        : 'No similar skills found in resume'}
                    </Typography>
                  </Box>

                  {hasSuggestions && (
                    <IconButton
                      size="small"
                      onClick={() => toggleExpanded(missingSkill.skill)}
                      sx={{ ml: 1 }}
                    >
                      {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                    </IconButton>
                  )}
                </Box>

                {/* Suggestions */}
                {hasSuggestions && (
                  <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                    <Box sx={{ mt: 1.5 }}>
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        sx={{ display: 'block', mb: 1, fontWeight: 500 }}
                      >
                        Suggested alternatives from resume:
                      </Typography>
                      <Stack spacing={1}>
                        {missingSkill.suggestions.map((suggestion, idx) => {
                          const reasonConfig = getSuggestionReasonConfig(suggestion.reason);
                          const confidencePercent = Math.round(suggestion.confidence * 100);

                          return (
                            <Box
                              key={idx}
                              sx={{
                                p: 1,
                                borderRadius: 0.75,
                                backgroundColor: 'background.paper',
                                border: '1px solid',
                                borderColor: 'divider',
                                transition: 'background-color 0.2s',
                                '&:hover': {
                                  backgroundColor: 'action.hover',
                                },
                              }}
                            >
                              <Box
                                sx={{
                                  display: 'flex',
                                  justifyContent: 'space-between',
                                  alignItems: 'flex-start',
                                  mb: 0.5,
                                }}
                              >
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                  <SuggestionIcon
                                    fontSize="small"
                                    sx={{ color: 'info.main', fontSize: '1rem' }}
                                  />
                                  <Typography
                                    variant="body2"
                                    fontWeight={600}
                                    color="text.primary"
                                  >
                                    {suggestion.skill}
                                  </Typography>
                                </Box>

                                <Stack direction="row" spacing={0.5} alignItems="center">
                                  <Tooltip title={reasonConfig.description} arrow>
                                    <Chip
                                      icon={reasonConfig.icon}
                                      label={reasonConfig.label}
                                      size="small"
                                      color={reasonConfig.color}
                                      variant="outlined"
                                      sx={{ fontSize: '0.65rem', height: 18 }}
                                    />
                                  </Tooltip>

                                  <Chip
                                    label={`${confidencePercent}%`}
                                    size="small"
                                    sx={{
                                      fontSize: '0.65rem',
                                      height: 18,
                                      fontWeight: 600,
                                      backgroundColor:
                                        suggestion.confidence >= 0.8
                                          ? 'success.light'
                                          : suggestion.confidence >= 0.65
                                          ? 'info.light'
                                          : suggestion.confidence >= 0.5
                                          ? 'warning.light'
                                          : 'error.light',
                                    }}
                                  />
                                </Stack>
                              </Box>

                              <SuggestionBar confidence={suggestion.confidence} />
                            </Box>
                          );
                        })}
                      </Stack>
                    </Box>
                  </Collapse>
                )}
              </Box>
            );
          })}
        </Stack>

        {hasMore && (
          <Box sx={{ mt: 2, textAlign: 'center' }}>
            <Typography variant="caption" color="text.secondary">
              Showing {maxDisplay} of {missingSkills.length} missing skills
            </Typography>
          </Box>
        )}
      </CardContent>
    </StyledCard>
  );
};

export default SkillGapAnalysis;
