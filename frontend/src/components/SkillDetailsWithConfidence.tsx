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
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';
import { styled } from '@emotion/styled';

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

const StyledCard = styled(Card)`
  margin-bottom: ${({ theme }) => theme.spacing.sm};
  height: 100%;
  display: flex;
  flex-direction: column;
`;

const ConfidenceBar = styled('div')<{ confidence: number; theme: any }>`
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
      confidence >= 0.9
        ? theme.colors.success.main
        : confidence >= 0.7
        ? theme.colors.primary.main
        : confidence >= 0.5
        ? theme.colors.warning.main
        : theme.colors.error.main};
    transition: width 0.3s ease;
  }
`;

const getMatchTypeConfig = (matchType: string) => {
  switch (matchType) {
    case 'direct':
      return {
        label: 'Direct',
        iconName: 'check-circle',
        color: 'success' as const,
        bgColor: 'success.light' as const,
        description: 'Exact match found in resume',
      };
    case 'synonym':
      return {
        label: 'Synonym',
        iconName: 'languages',
        color: 'info' as const,
        bgColor: 'info.light' as const,
        description: 'Matched through known synonyms',
      };
    case 'fuzzy':
      return {
        label: 'Fuzzy',
        iconName: 'search',
        color: 'warning' as const,
        bgColor: 'warning.light' as const,
        description: 'Partial match (typo or variation)',
      };
    case 'context':
      return {
        label: 'Context',
        iconName: 'brain',
        color: 'secondary' as const,
        bgColor: 'secondary.light' as const,
        description: 'Matched based on domain context',
      };
    case 'compound':
      return {
        label: 'Compound',
        iconName: 'wand-sparkles',
        color: 'primary' as const,
        bgColor: 'primary.light' as const,
        description: 'Compound skill match',
      };
    case 'language_hierarchy':
      return {
        label: 'Hierarchy',
        iconName: 'brain',
        color: 'info' as const,
        bgColor: 'info.light' as const,
        description: 'Matched through language hierarchy',
      };
    default:
      return {
        label: 'Unknown',
        iconName: 'check-circle',
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
      <Box css={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
        <Typography css={{ ml: 2 }}>
          Loading skill details...
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

  if (!skills || skills.length === 0) {
    return (
      <Box css={{ textAlign: 'center', py: 4 }}>
        <Icon name="check-circle" css={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
        <Typography color="text.secondary">
          No matched skills
        </Typography>
        <Typography color="text.secondary">
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
          css={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            mb: 2,
          }}
        >
          <Typography fontWeight={600}>
            {title}
          </Typography>
          <Chip
            label={`${skills.length} skills`}
            size="small"
            color="primary"
            variant="outlined"
          />
        </Box>

        <Divider css={{ mb: 2 }} />

        <Stack spacing={2}>
          {displaySkills.map((skillDetail, index) => {
            const matchConfig = getMatchTypeConfig(skillDetail.match_type);
            const confidencePercent = Math.round(skillDetail.confidence * 100);

            return (
              <Box
                key={`${skillDetail.skill}-${index}`}
                css={{
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
                  css={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    mb: 1,
                  }}
                >
                  <Box css={{ flex: 1 }}>
                    <Typography
                      css={{ mb: 0.5, fontWeight: 600 }}
                    >
                      {skillDetail.skill}
                      {skillDetail.matched_as &&
                        skillDetail.matched_as !== skillDetail.skill && (
                          <Typography
                            as="span"
                            color="text.secondary"
                            css={{ ml: 1, fontWeight: 400 }}
                          >
                            (matched as "{skillDetail.matched_as}")
                          </Typography>
                        )}
                    </Typography>

                    <Stack css={{ display: 'flex', gap: 0.5, alignItems: 'center' }}>
                      <Tooltip title={matchConfig.description} arrow>
                        <Chip
                          iconName={matchConfig.iconName}
                          label={matchConfig.label}
                          size="small"
                          color={matchConfig.color}
                          variant="outlined"
                          css={{ fontSize: '0.7rem', height: 20 }}
                        />
                      </Tooltip>

                      <Chip
                        label={`${confidencePercent}%`}
                        size="small"
                        css={{
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
                  <Box css={{ mt: 1 }}>
                    <Typography
                      color="text.secondary"
                      css={{ display: 'block', mb: 0.5, fontWeight: 500 }}
                    >
                      Found in resume:
                    </Typography>
                    {skillDetail.locations.slice(0, 2).map((location, idx) => (
                      <Box
                        key={idx}
                        css={{
                          p: 0.75,
                          mt: idx > 0 ? 0.5 : 0,
                          backgroundColor: 'background.paper',
                          borderRadius: 0.5,
                          border: '1px solid',
                          borderColor: 'divider',
                        }}
                      >
                        <Typography
                          css={{
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
                        color="text.secondary"
                        css={{ display: 'block', mt: 0.5, fontStyle: 'italic' }}
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
          <Box css={{ mt: 2, textAlign: 'center' }}>
            <Typography color="text.secondary">
              Showing {maxDisplay} of {skills.length} matched skills
            </Typography>
          </Box>
        )}
      </CardContent>
    </StyledCard>
  );
};

export default SkillDetailsWithConfidence;
