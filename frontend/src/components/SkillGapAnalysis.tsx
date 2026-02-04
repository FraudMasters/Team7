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
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';
import { styled } from '@emotion/styled';

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

const StyledCard = styled(Card)`
  margin-bottom: ${({ theme }) => theme.spacing.sm};
  height: 100%;
  display: flex;
  flex-direction: column;
`;

const SuggestionBar = styled('div')<{ confidence: number; theme: any }>`
  height: 4px;
  border-radius: 2px;
  background-color: ${({ theme }) => theme.colors.grey[200]};
  position: relative;
  overflow: hidden;
  margin-top: ${({ theme }) => theme.spacing.xs};

  &::after {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: ${({ confidence }) => confidence * 100}%;
    background-color: ${({ confidence, theme }) =>
      confidence >= 0.8
        ? theme.colors.success.main
        : confidence >= 0.65
        ? theme.colors.info.main
        : confidence >= 0.5
        ? theme.colors.warning.main
        : theme.colors.error.main};
    transition: width 0.3s ease;
  }
`;

const getSuggestionReasonConfig = (reason: string) => {
  switch (reason) {
    case 'synonym':
      return {
        label: 'Synonym',
        iconName: 'languages',
        color: 'success' as const,
        bgColor: 'success.light' as const,
        description: 'Known synonym or equivalent term',
      };
    case 'same_category':
      return {
        label: 'Category',
        iconName: 'folder-tree',
        color: 'info' as const,
        bgColor: 'info.light' as const,
        description: 'From the same skill category',
      };
    case 'related':
      return {
        label: 'Related',
        iconName: 'link',
        color: 'secondary' as const,
        bgColor: 'secondary.light' as const,
        description: 'Commonly used together',
      };
    case 'fuzzy_match':
      return {
        label: 'Similar',
        iconName: 'search',
        color: 'warning' as const,
        bgColor: 'warning.light' as const,
        description: 'Similar name or variation',
      };
    default:
      return {
        label: 'Suggestion',
        iconName: 'brain',
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
      <Box css={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
        <Typography css={{ ml: 2 }}>
          Analyzing skill gaps...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" css={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!missingSkills || missingSkills.length === 0) {
    return (
      <Box css={{ textAlign: 'center', py: 4 }}>
        <Icon name="lightbulb" css={{ fontSize: 48, color: 'success.main', mb: 2 }} />
        <Typography color="text.secondary">
          No Missing Skills
        </Typography>
        <Typography color="text.secondary">
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
          css={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            mb: 2,
          }}
        >
          <Box css={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Icon name="x-circle" css={{ color: 'warning.main' }} />
            <Typography fontWeight={600}>
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

        <Divider css={{ mb: 2 }} />

        <Stack spacing={2}>
          {displaySkills.map((missingSkill, index) => {
            const isExpanded = expandedSkills.has(missingSkill.skill);
            const hasSuggestions = missingSkill.suggestions && missingSkill.suggestions.length > 0;

            return (
              <Box
                key={`${missingSkill.skill}-${index}`}
                css={{
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
                  css={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <Box css={{ flex: 1 }}>
                    <Typography
                      css={{ mb: 0.5, fontWeight: 600 }}
                      color="warning.dark"
                    >
                      {missingSkill.skill}
                    </Typography>
                    <Typography color="text.secondary">
                      {hasSuggestions
                        ? `${missingSkill.suggestions.length} suggestion${missingSkill.suggestions.length > 1 ? 's' : ''} available`
                        : 'No similar skills found in resume'}
                    </Typography>
                  </Box>

                  {hasSuggestions && (
                    <IconButton
                      size="small"
                      onClick={() => toggleExpanded(missingSkill.skill)}
                      css={{ ml: 1 }}
                    >
                      <Icon name={isExpanded ? 'chevron-up' : 'chevron-down'} />
                    </IconButton>
                  )}
                </Box>

                {/* Suggestions */}
                {hasSuggestions && (
                  <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                    <Box css={{ mt: 1.5 }}>
                      <Typography
                        color="text.secondary"
                        css={{ display: 'block', mb: 1, fontWeight: 500 }}
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
                              css={{
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
                                css={{
                                  display: 'flex',
                                  justifyContent: 'space-between',
                                  alignItems: 'flex-start',
                                  mb: 0.5,
                                }}
                              >
                                <Box css={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                  <Icon
                                    name="lightbulb"
                                    css={{ color: 'info.main', fontSize: '1rem' }}
                                  />
                                  <Typography
                                    fontWeight={600}
                                    color="text.primary"
                                  >
                                    {suggestion.skill}
                                  </Typography>
                                </Box>

                                <Stack css={{ display: 'flex', gap: 0.5, alignItems: 'center' }}>
                                  <Tooltip title={reasonConfig.description} arrow>
                                    <Chip
                                      iconName={reasonConfig.iconName}
                                      label={reasonConfig.label}
                                      size="small"
                                      color={reasonConfig.color}
                                      variant="outlined"
                                      css={{ fontSize: '0.65rem', height: 18 }}
                                    />
                                  </Tooltip>

                                  <Chip
                                    label={`${confidencePercent}%`}
                                    size="small"
                                    css={{
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
          <Box css={{ mt: 2, textAlign: 'center' }}>
            <Typography color="text.secondary">
              Showing {maxDisplay} of {missingSkills.length} missing skills
            </Typography>
          </Box>
        )}
      </CardContent>
    </StyledCard>
  );
};

export default SkillGapAnalysis;
