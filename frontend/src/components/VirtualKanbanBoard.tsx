import React, { useRef, useCallback, useMemo } from 'react';
import { FixedSizeList as List, ListChildComponentProps } from 'react-window';
import { Box, Paper, Typography, Chip, Checkbox, IconButton, CircularProgress } from '@/components/ui';
import { Icon } from '@/components/ui/primitives';
import { Draggable, Droppable } from '@hello-pangea/dnd';

interface Candidate {
  id: string;
  filename: string;
  status: string;
  created_at: string;
  skills: string[];
  email?: string;
  phone?: string;
  match_percentage?: number;
  vacancy_title?: string;
}

interface Stage {
  id: string;
  name: string;
  key: string;
}

interface VirtualKanbanBoardProps {
  stages: Stage[];
  candidatesByStage: Record<string, Candidate[]>;
  onCardClick: (candidate: Candidate, index: number, event: React.MouseEvent) => void;
  selectedCandidateIndex: number;
  allFilteredCandidates: Candidate[];
  selectedCandidateIds: Set<string>;
  onToggleSelection: (candidateId: string) => void;
  dragLoading: boolean;
  movingCandidateIds: Set<string>;
  isMobile: boolean;
  isDesktop: boolean;
  getTitleFromFilename: (filename: string) => string;
  t: (key: string) => string;
  isAllSelectedInStage: (stageId: string) => boolean;
  onSelectAllInStage: (stageId: string) => void;
  onClearStageSelection: (stageId: string) => void;
  candidatesByStageUnfiltered: Record<string, Candidate[]>;
}

/**
 * VirtualKanbanBoard Component
 *
 * Implements virtual scrolling for large candidate lists in kanban columns.
 * Uses react-window to only render visible candidates, improving performance
 * with 100+ candidates.
 */
const VirtualKanbanBoard: React.FC<VirtualKanbanBoardProps> = ({
  stages,
  candidatesByStage,
  onCardClick,
  selectedCandidateIndex,
  allFilteredCandidates,
  selectedCandidateIds,
  onToggleSelection,
  dragLoading,
  movingCandidateIds,
  isMobile,
  isDesktop,
  getTitleFromFilename,
  t,
  isAllSelectedInStage,
  onSelectAllInStage,
  onClearStageSelection,
  candidatesByStageUnfiltered,
}) => {
  // Estimated card height including margin
  const ITEM_SIZE = 180;

  /**
   * Render a single candidate card for virtual list
   */
  const renderCandidateCard = useCallback(
    ({ index, data, style }: ListChildComponentProps) => {
      const { candidates, stageId } = data as { candidates: Candidate[]; stageId: string };
      const candidate = candidates[index];
      const globalIndex = allFilteredCandidates.indexOf(candidate);
      const isSelected = globalIndex === selectedCandidateIndex;
      const isBatchSelected = selectedCandidateIds.has(candidate.id);
      const isMoving = movingCandidateIds.has(candidate.id);

      return (
        <div style={style}>
          <Draggable
            key={candidate.id}
            draggableId={candidate.id}
            index={index}
            isDragDisabled={dragLoading || isMoving}
          >
            {(provided, snapshot) => (
              <div
                ref={provided.innerRef}
                {...provided.draggableProps}
                {...provided.dragHandleProps}
                style={{
                  ...provided.draggableProps.style,
                  marginBottom: 8,
                }}
              >
                <Box
                  onClick={(e) => onCardClick(candidate, globalIndex, e)}
                  sx={{
                    bgcolor: 'background.paper',
                    borderRadius: 1,
                    p: 2,
                    cursor: isMoving ? 'wait' : snapshot.isDragging ? 'grabbing' : 'pointer',
                    transition: 'all 0.2s',
                    border: isSelected || isBatchSelected ? '3px solid' : '2px solid transparent',
                    borderColor: isBatchSelected ? 'secondary.main' : isSelected ? 'primary.main' : 'divider',
                    boxShadow: isSelected || isBatchSelected || snapshot.isDragging ? 8 : 1,
                    transform: isSelected || isBatchSelected ? 'translateY(-4px)' : 'none',
                    opacity: isMoving ? 0.6 : snapshot.isDragging ? 0.8 : 1,
                    '&:hover': {
                      boxShadow: isMoving ? 1 : 4,
                      transform: isMoving ? 'none' : 'translateY(-2px)',
                    },
                    position: 'relative',
                    minHeight: { xs: 120, sm: 'auto' },
                    pointerEvents: isMoving ? 'none' : 'auto',
                  }}
                  tabIndex={0}
                  aria-selected={isSelected || isBatchSelected}
                  aria-busy={isMoving}
                >
                  {/* Loading overlay for moving cards */}
                  {isMoving && (
                    <Box
                      sx={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        bgcolor: 'rgba(255, 255, 255, 0.8)',
                        borderRadius: 1,
                        zIndex: 10,
                      }}
                    >
                      <CircularProgress size={24} />
                    </Box>
                  )}
                  {/* Drag handle and checkbox */}
                  <Box
                    sx={{
                      position: 'absolute',
                      top: { xs: 6, sm: 8 },
                      right: { xs: 6, sm: 8 },
                      zIndex: 1,
                      display: 'flex',
                      gap: { xs: 0.25, sm: 0.5 },
                      alignItems: 'center',
                    }}
                  >
                    <Checkbox
                      size="small"
                      checked={isBatchSelected}
                      onChange={(e) => {
                        e.stopPropagation();
                        onToggleSelection(candidate.id);
                      }}
                      onClick={(e) => e.stopPropagation()}
                      sx={{
                        p: { xs: 0.25, sm: 0.5 },
                        '& svg': {
                          fontSize: { xs: 18, sm: 20 },
                        },
                      }}
                    />
                    <Box
                      {...provided.dragHandleProps}
                      sx={{
                        cursor: 'grab',
                        '&:active': { cursor: 'grabbing' },
                        p: { xs: 0.5, sm: 0 },
                        ml: { xs: 0.25, sm: 0 },
                      }}
                    >
                      <svg
                        width="24"
                        height="24"
                        viewBox="0 0 24 24"
                        fill="currentColor"
                        style={{ color: 'text.secondary', fontSize: { xs: 20, sm: 24 } }}
                      >
                        <circle cx="9" cy="6" r="1.5" />
                        <circle cx="15" cy="6" r="1.5" />
                        <circle cx="9" cy="12" r="1.5" />
                        <circle cx="15" cy="12" r="1.5" />
                        <circle cx="9" cy="18" r="1.5" />
                        <circle cx="15" cy="18" r="1.5" />
                      </svg>
                    </Box>
                  </Box>

                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <PersonIcon sx={{ mr: 1, color: 'primary.main', fontSize: { xs: 18, sm: 20 } }} />
                    <Typography
                      variant="subtitle1"
                      fontWeight={600}
                      sx={{ fontSize: { xs: '0.9rem', sm: '1rem' } }}
                    >
                      {getTitleFromFilename(candidate.filename)}
                    </Typography>
                  </Box>

                  {candidate.match_percentage && (
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <Chip
                        label={`${candidate.match_percentage}% ${t('candidatesKanban.match')}`}
                        size="small"
                        color={
                          candidate.match_percentage >= 80
                            ? 'success'
                            : candidate.match_percentage >= 60
                            ? 'warning'
                            : 'default'
                        }
                        sx={{
                          mr: 1,
                          fontSize: { xs: '0.7rem', sm: '0.75rem' },
                          height: { xs: 20, sm: 24 },
                        }}
                      />
                    </Box>
                  )}

                  {candidate.skills && candidate.skills.length > 0 && (
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' } }}>
                        {t('candidatesKanban.skills')}:
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                        {candidate.skills.slice(0, 3).map((skill, i) => (
                          <Chip
                            key={i}
                            label={skill}
                            size="small"
                            variant="outlined"
                            sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' }, height: { xs: 20, sm: 24 } }}
                          />
                        ))}
                        {candidate.skills.length > 3 && (
                          <Chip
                            label={`+${candidate.skills.length - 3}`}
                            size="small"
                            variant="outlined"
                            sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' }, height: { xs: 20, sm: 24 } }}
                          />
                        )}
                      </Box>
                    </Box>
                  )}

                  {candidate.vacancy_title && (
                    <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                      <WorkIcon sx={{ fontSize: { xs: 14, sm: 16 }, mr: 0.5, color: 'text.secondary' }} />
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' } }}>
                        {candidate.vacancy_title}
                      </Typography>
                    </Box>
                  )}
                </Box>
              </div>
            )}
          </Draggable>
        </div>
      );
    },
    [
      allFilteredCandidates,
      selectedCandidateIndex,
      selectedCandidateIds,
      onCardClick,
      onToggleSelection,
      dragLoading,
      movingCandidateIds,
      getTitleFromFilename,
      t,
      isMobile,
    ]
  );

  /**
   * Render stage column with virtual scrolling
   */
  const renderStageColumn = useCallback(
    (stage: Stage) => {
      const candidates = candidatesByStage[stage.id] || [];
      const candidateCount = candidates.length;

      // Use virtual scrolling only if more than 15 candidates
      const useVirtualization = isDesktop && candidateCount > 15;

      // Calculate height for virtual list
      const listHeight = useVirtualization
        ? Math.min(candidateCount * ITEM_SIZE + 50, 600) // Cap at 600px height
        : 'auto';

      return (
        <Box
          key={stage.id}
          sx={{
            minWidth: {
              xs: 280,
              sm: 280,
              md: 260,
              lg: 0,
            },
            maxWidth: {
              xs: 320,
              sm: 320,
              md: 300,
              lg: 'none',
            },
            flex: {
              xs: '0 0 auto',
              sm: '0 0 auto',
              lg: '1 1 0',
            },
            scrollSnapAlign: { xs: 'start', sm: 'start', lg: 'none' },
            willChange: 'transform',
          }}
        >
          {/* Stage Header */}
          <Paper
            sx={{
              p: { xs: 1.5, sm: 2 },
              mb: 2,
              bgcolor: 'primary.main',
              color: 'primary.contrastText',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: { xs: 'flex-start', sm: 'center' },
              flexDirection: { xs: 'column', sm: 'row' },
              gap: { xs: 1, sm: 0 },
            }}
          >
            <Box sx={{ width: { xs: '100%', sm: 'auto' } }}>
              <Typography variant="h6" fontWeight={600} sx={{ fontSize: { xs: '1.1rem', sm: '1.25rem' } }}>
                {t(stage.key)}
              </Typography>
              <Typography variant="caption" sx={{ fontSize: { xs: '0.7rem', sm: '0.75rem' } }}>
                {candidateCount} {t('candidatesKanban.candidates')}
              </Typography>
            </Box>

            {candidateCount > 0 && (
              <button
                onClick={() => {
                  if (isAllSelectedInStage(stage.id)) {
                    onClearStageSelection(stage.id);
                  } else {
                    onSelectAllInStage(stage.id);
                  }
                }}
                style={{
                  background: 'transparent',
                  border: '1px solid currentColor',
                  color: 'currentColor',
                  borderRadius: '4px',
                  padding: '4px 12px',
                  fontSize: isMobile ? '0.7rem' : '0.75rem',
                  cursor: 'pointer',
                  minWidth: isMobile ? 'auto' : '64px',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'rgba(0, 0, 0, 0.1)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'transparent';
                }}
              >
                {isAllSelectedInStage(stage.id) ? 'Deselect All' : 'Select All'}
              </button>
            )}
          </Paper>

          {/* Candidate Cards with Virtual Scrolling */}
          <Droppable droppableId={stage.id} mode={useVirtualization ? 'virtual' : undefined}>
            {(provided, snapshot) => (
              <Box
                {...provided.droppableProps}
                ref={provided.innerRef}
                sx={{
                  minHeight: { xs: 200, sm: 250, lg: 300 },
                  maxHeight: isDesktop ? 600 : 'calc(100vh - 280px)',
                  overflowY: 'auto',
                  bgcolor: snapshot.isDraggingOver ? 'action.hover' : 'transparent',
                  borderRadius: 1,
                  transition: 'background-color 0.2s',
                }}
              >
                {candidateCount > 0 ? (
                  useVirtualization ? (
                    <List
                      height={listHeight}
                      itemCount={candidateCount}
                      itemSize={ITEM_SIZE}
                      width="100%"
                      itemData={{ candidates, stageId: stage.id }}
                      outerRef={provided.innerRef}
                    >
                      {renderCandidateCard}
                    </List>
                  ) : (
                    candidates.map((candidate, index) => {
                      const globalIndex = allFilteredCandidates.indexOf(candidate);
                      const isSelected = globalIndex === selectedCandidateIndex;
                      const isBatchSelected = selectedCandidateIds.has(candidate.id);
                      const isMoving = movingCandidateIds.has(candidate.id);

                      return (
                        <Draggable
                          key={candidate.id}
                          draggableId={candidate.id}
                          index={index}
                          isDragDisabled={dragLoading || isMoving}
                        >
                          {(provided, snapshot) => (
                            <div
                              ref={provided.innerRef}
                              {...provided.draggableProps}
                              {...provided.dragHandleProps}
                              style={{
                                ...provided.draggableProps.style,
                                marginBottom: 8,
                              }}
                            >
                              <Box
                                onClick={(e) => onCardClick(candidate, globalIndex, e)}
                                sx={{
                                  bgcolor: 'background.paper',
                                  borderRadius: 1,
                                  p: 2,
                                  cursor: isMoving ? 'wait' : snapshot.isDragging ? 'grabbing' : 'pointer',
                                  transition: 'all 0.2s',
                                  border: isSelected || isBatchSelected ? '3px solid' : '2px solid transparent',
                                  borderColor: isBatchSelected ? 'secondary.main' : isSelected ? 'primary.main' : 'divider',
                                  boxShadow: isSelected || isBatchSelected || snapshot.isDragging ? 8 : 1,
                                  transform: isSelected || isBatchSelected ? 'translateY(-4px)' : 'none',
                                  opacity: isMoving ? 0.6 : snapshot.isDragging ? 0.8 : 1,
                                  '&:hover': {
                                    boxShadow: isMoving ? 1 : 4,
                                    transform: isMoving ? 'none' : 'translateY(-2px)',
                                  },
                                  position: 'relative',
                                  minHeight: { xs: 120, sm: 'auto' },
                                  pointerEvents: isMoving ? 'none' : 'auto',
                                }}
                                tabIndex={0}
                                aria-selected={isSelected || isBatchSelected}
                                aria-busy={isMoving}
                              >
                                {/* Loading overlay for moving cards */}
                                {isMoving && (
                                  <Box
                                    sx={{
                                      position: 'absolute',
                                      top: 0,
                                      left: 0,
                                      right: 0,
                                      bottom: 0,
                                      display: 'flex',
                                      alignItems: 'center',
                                      justifyContent: 'center',
                                      bgcolor: 'rgba(255, 255, 255, 0.8)',
                                      borderRadius: 1,
                                      zIndex: 10,
                                    }}
                                  >
                                    <CircularProgress size={24} />
                                  </Box>
                                )}
                                {/* Drag handle and checkbox */}
                                <Box
                                  sx={{
                                    position: 'absolute',
                                    top: { xs: 6, sm: 8 },
                                    right: { xs: 6, sm: 8 },
                                    zIndex: 1,
                                    display: 'flex',
                                    gap: { xs: 0.25, sm: 0.5 },
                                    alignItems: 'center',
                                  }}
                                >
                                  <Checkbox
                                    size="small"
                                    checked={isBatchSelected}
                                    onChange={(e) => {
                                      e.stopPropagation();
                                      onToggleSelection(candidate.id);
                                    }}
                                    onClick={(e) => e.stopPropagation()}
                                    sx={{
                                      p: { xs: 0.25, sm: 0.5 },
                                      '& svg': {
                                        fontSize: { xs: 18, sm: 20 },
                                      },
                                    }}
                                  />
                                  <Box
                                    {...provided.dragHandleProps}
                                    sx={{
                                      cursor: 'grab',
                                      '&:active': { cursor: 'grabbing' },
                                      p: { xs: 0.5, sm: 0 },
                                      ml: { xs: 0.25, sm: 0 },
                                    }}
                                  >
                                    <svg
                                      width="24"
                                      height="24"
                                      viewBox="0 0 24 24"
                                      fill="currentColor"
                                      style={{ color: 'text.secondary', fontSize: { xs: 20, sm: 24 } }}
                                    >
                                      <circle cx="9" cy="6" r="1.5" />
                                      <circle cx="15" cy="6" r="1.5" />
                                      <circle cx="9" cy="12" r="1.5" />
                                      <circle cx="15" cy="12" r="1.5" />
                                      <circle cx="9" cy="18" r="1.5" />
                                      <circle cx="15" cy="18" r="1.5" />
                                    </svg>
                                  </Box>
                                </Box>

                                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                  <PersonIcon sx={{ mr: 1, color: 'primary.main', fontSize: { xs: 18, sm: 20 } }} />
                                  <Typography
                                    variant="subtitle1"
                                    fontWeight={600}
                                    sx={{ fontSize: { xs: '0.9rem', sm: '1rem' } }}
                                  >
                                    {getTitleFromFilename(candidate.filename)}
                                  </Typography>
                                </Box>

                                {candidate.match_percentage && (
                                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                    <Chip
                                      label={`${candidate.match_percentage}% ${t('candidatesKanban.match')}`}
                                      size="small"
                                      color={
                                        candidate.match_percentage >= 80
                                          ? 'success'
                                          : candidate.match_percentage >= 60
                                          ? 'warning'
                                          : 'default'
                                      }
                                      sx={{
                                        mr: 1,
                                        fontSize: { xs: '0.7rem', sm: '0.75rem' },
                                        height: { xs: 20, sm: 24 },
                                      }}
                                    />
                                  </Box>
                                )}

                                {candidate.skills && candidate.skills.length > 0 && (
                                  <Box sx={{ mb: 1 }}>
                                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' } }}>
                                      {t('candidatesKanban.skills')}:
                                    </Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                                      {candidate.skills.slice(0, 3).map((skill, i) => (
                                        <Chip
                                          key={i}
                                          label={skill}
                                          size="small"
                                          variant="outlined"
                                          sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' }, height: { xs: 20, sm: 24 } }}
                                        />
                                      ))}
                                      {candidate.skills.length > 3 && (
                                        <Chip
                                          label={`+${candidate.skills.length - 3}`}
                                          size="small"
                                          variant="outlined"
                                          sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' }, height: { xs: 20, sm: 24 } }}
                                        />
                                      )}
                                    </Box>
                                  </Box>
                                )}

                                {candidate.vacancy_title && (
                                  <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                                    <WorkIcon sx={{ fontSize: { xs: 14, sm: 16 }, mr: 0.5, color: 'text.secondary' }} />
                                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' } }}>
                                      {candidate.vacancy_title}
                                    </Typography>
                                  </Box>
                                )}
                              </Box>
                            </div>
                          )}
                        </Draggable>
                      );
                    })
                  )
                ) : (
                  <Paper sx={{ p: 3, textAlign: 'center', bgcolor: 'action.hover' }}>
                    <Typography variant="body2" color="text.secondary">
                      {t('candidatesKanban.noCandidates')}
                    </Typography>
                  </Paper>
                )}
                {provided.placeholder}
              </Box>
            )}
          </Droppable>
        </Box>
      );
    },
    [
      candidatesByStage,
      allFilteredCandidates,
      selectedCandidateIndex,
      selectedCandidateIds,
      onCardClick,
      onToggleSelection,
      dragLoading,
      movingCandidateIds,
      isMobile,
      isDesktop,
      getTitleFromFilename,
      t,
      isAllSelectedInStage,
      onSelectAllInStage,
      onClearStageSelection,
      renderCandidateCard,
      ITEM_SIZE,
    ]
  );

  return (
    <Box
      sx={{
        display: 'flex',
        gap: { xs: 1.5, sm: 2, lg: 2.5 },
        overflowX: { xs: 'auto', lg: 'visible' },
        overflowY: 'hidden',
        pb: { xs: 2, sm: 0 },
        scrollSnapType: { xs: 'x mandatory', sm: 'none' },
        '&::-webkit-scrollbar': {
          height: { xs: 8, sm: 0 },
        },
        '&::-webkit-scrollbar-track': {
          bgcolor: 'background.default',
          borderRadius: 1,
        },
        '&::-webkit-scrollbar-thumb': {
          bgcolor: 'primary.main',
          borderRadius: 1,
          '&:hover': {
            bgcolor: 'primary.dark',
          },
        },
      }}
    >
      {stages.map((stage) => renderStageColumn(stage))}
    </Box>
  );
};

export default VirtualKanbanBoard;
