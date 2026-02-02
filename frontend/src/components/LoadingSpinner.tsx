import React from 'react';
import {
  Box,
  CircularProgress,
  Skeleton,
  SkeletonProps,
  Typography,
  useTheme,
  alpha,
} from '@mui/material';

export type LoadingSpinnerVariant =
  | 'spinner'
  | 'cards'
  | 'list'
  | 'table'
  | 'form'
  | 'page'
  | 'upload'
  | 'analysis'
  | 'vacancy-details'
  | 'dashboard'
  | 'candidate-search'
  | 'custom';

export interface LoadingSpinnerProps {
  /**
   * The variant of loading indicator to display
   * @default 'spinner'
   */
  variant?: LoadingSpinnerVariant;

  /**
   * Number of skeleton items to show (for list, cards, table variants)
   * @default 3
   */
  count?: number;

  /**
   * Size of the circular progress spinner (for 'spinner' variant)
   * @default 40
   */
  size?: number;

  /**
   * Optional loading message to display
   */
  message?: string;

  /**
   * Whether to center the loading indicator
   * @default true
   */
  centered?: boolean;

  /**
   * Custom skeleton elements (for 'custom' variant)
   */
  customSkeleton?: React.ReactNode;

  /**
   * Additional props to pass to Skeleton components
   */
  skeletonProps?: SkeletonProps;
}

/**
 * LoadingSpinner Component
 *
 * A flexible loading indicator component with multiple skeleton screen variants
 * for improved perceived performance across different content types.
 *
 * @example
 * ```tsx
 * // Simple spinner
 * <LoadingSpinner />
 *
 * // Card skeleton for vacancy lists
 * <LoadingSpinner variant="cards" count={6} />
 *
 * // Table skeleton for data tables
 * <LoadingSpinner variant="table" count={10} />
 *
 * // Form skeleton
 * <LoadingSpinner variant="form" message="Loading form..." />
 *
 * // Upload page skeleton
 * <LoadingSpinner variant="upload" />
 *
 * // Analysis results skeleton
 * <LoadingSpinner variant="analysis" />
 *
 * // Dashboard skeleton
 * <LoadingSpinner variant="dashboard" />
 *
 * // Candidate search skeleton
 * <LoadingSpinner variant="candidate-search" count={5} />
 * ```
 */
const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  variant = 'spinner',
  count = 3,
  size = 40,
  message,
  centered = true,
  customSkeleton,
  skeletonProps,
}) => {
  const theme = useTheme();

  // Common skeleton animation props
  const skeletonBaseProps: SkeletonProps = {
    animation: 'wave',
    ...skeletonProps,
  };

  // Simple circular progress spinner
  if (variant === 'spinner') {
    const content = (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 2,
          ...(centered && {
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
          }),
        }}
      >
        <CircularProgress size={size} />
        {message && (
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ textAlign: 'center' }}
          >
            {message}
          </Typography>
        )}
      </Box>
    );

    return centered ? (
      <Box
        sx={{
          position: 'relative',
          minHeight: 200,
          width: '100%',
        }}
      >
        {content}
      </Box>
    ) : (
      content
    );
  }

  // Custom skeleton variant
  if (variant === 'custom') {
    return <>{customSkeleton}</>;
  }

  // Card skeleton - for card-based layouts (vacancy cards, candidate cards, etc.)
  if (variant === 'cards') {
    return (
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: {
            xs: '1fr',
            sm: 'repeat(2, 1fr)',
            md: 'repeat(3, 1fr)',
          },
          gap: 2,
          width: '100%',
        }}
      >
        {Array.from({ length: count }).map((_, index) => (
          <Box
            key={index}
            sx={{
              p: 2,
              bgcolor: alpha(theme.palette.background.paper, 0.5),
              borderRadius: 1,
              border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
            }}
          >
            <Skeleton
              {...skeletonBaseProps}
              variant="rectangular"
              height={60}
              sx={{ mb: 2 }}
            />
            <Skeleton
              {...skeletonBaseProps}
              variant="text"
              width="60%"
              sx={{ mb: 1 }}
            />
            <Skeleton
              {...skeletonBaseProps}
              variant="text"
              width="80%"
              sx={{ mb: 2 }}
            />
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Skeleton
                {...skeletonBaseProps}
                variant="rectangular"
                width={60}
                height={24}
              />
              <Skeleton
                {...skeletonBaseProps}
                variant="rectangular"
                width={60}
                height={24}
              />
              <Skeleton
                {...skeletonBaseProps}
                variant="rectangular"
                width={60}
                height={24}
              />
            </Box>
          </Box>
        ))}
      </Box>
    );
  }

  // List skeleton - for list-based layouts
  if (variant === 'list') {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, width: '100%' }}>
        {Array.from({ length: count }).map((_, index) => (
          <Box
            key={index}
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 2,
              p: 2,
              bgcolor: alpha(theme.palette.background.paper, 0.5),
              borderRadius: 1,
            }}
          >
            <Skeleton
              {...skeletonBaseProps}
              variant="circular"
              width={48}
              height={48}
            />
            <Box sx={{ flex: 1 }}>
              <Skeleton
                {...skeletonBaseProps}
                variant="text"
                width="70%"
                sx={{ mb: 1 }}
              />
              <Skeleton
                {...skeletonBaseProps}
                variant="text"
                width="40%"
              />
            </Box>
            <Skeleton
              {...skeletonBaseProps}
              variant="rectangular"
              width={80}
              height={32}
            />
          </Box>
        ))}
      </Box>
    );
  }

  // Table skeleton - for table-based layouts
  if (variant === 'table') {
    return (
      <Box sx={{ width: '100%' }}>
        {/* Table header */}
        <Box
          sx={{
            display: 'flex',
            gap: 2,
            p: 2,
            borderBottom: `1px solid ${theme.palette.divider}`,
            bgcolor: alpha(theme.palette.action.hover, 0.5),
          }}
        >
          <Skeleton {...skeletonBaseProps} variant="text" width="20%" />
          <Skeleton {...skeletonBaseProps} variant="text" width="25%" />
          <Skeleton {...skeletonBaseProps} variant="text" width="15%" />
          <Skeleton {...skeletonBaseProps} variant="text" width="15%" />
          <Skeleton {...skeletonBaseProps} variant="text" width="15%" />
          <Skeleton {...skeletonBaseProps} variant="text" width="10%" />
        </Box>
        {/* Table rows */}
        {Array.from({ length: count }).map((_, index) => (
          <Box
            key={index}
            sx={{
              display: 'flex',
              gap: 2,
              p: 2,
              borderBottom: `1px solid ${alpha(theme.palette.divider, 0.5)}`,
            }}
          >
            <Skeleton {...skeletonBaseProps} variant="text" width="20%" />
            <Skeleton {...skeletonBaseProps} variant="text" width="25%" />
            <Skeleton {...skeletonBaseProps} variant="text" width="15%" />
            <Skeleton {...skeletonBaseProps} variant="text" width="15%" />
            <Skeleton {...skeletonBaseProps} variant="text" width="15%" />
            <Skeleton {...skeletonBaseProps} variant="text" width="10%" />
          </Box>
        ))}
      </Box>
    );
  }

  // Form skeleton - for form-based layouts
  if (variant === 'form') {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          gap: 3,
          maxWidth: 600,
          width: '100%',
          p: 3,
        }}
      >
        {message && (
          <Typography variant="h6" gutterBottom>
            {message}
          </Typography>
        )}
        {/* Form fields */}
        {Array.from({ length: 5 }).map((_, index) => (
          <Box key={index}>
            <Skeleton
              {...skeletonBaseProps}
              variant="text"
              width="30%"
              sx={{ mb: 1 }}
            />
            <Skeleton
              {...skeletonBaseProps}
              variant="rectangular"
              height={56}
              sx={{ borderRadius: 1 }}
            />
          </Box>
        ))}
        {/* Form actions */}
        <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
          <Skeleton
            {...skeletonBaseProps}
            variant="rectangular"
            width={120}
            height={36}
            sx={{ borderRadius: 1 }}
          />
          <Skeleton
            {...skeletonBaseProps}
            variant="rectangular"
            width={120}
            height={36}
            sx={{ borderRadius: 1 }}
          />
        </Box>
      </Box>
    );
  }

  // Full page skeleton - for complete page layouts
  if (variant === 'page') {
    return (
      <Box sx={{ width: '100%', p: 3 }}>
        {/* Page header */}
        <Box sx={{ mb: 4 }}>
          <Skeleton
            {...skeletonBaseProps}
            variant="text"
            width="40%"
            height={40}
            sx={{ mb: 2 }}
          />
          <Skeleton
            {...skeletonBaseProps}
            variant="rectangular"
            width="100%"
            height={100}
            sx={{ borderRadius: 1 }}
          />
        </Box>
        {/* Page content grid */}
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: {
              xs: '1fr',
              md: 'repeat(2, 1fr)',
              lg: 'repeat(3, 1fr)',
            },
            gap: 2,
          }}
        >
          {Array.from({ length: count || 6 }).map((_, index) => (
            <Box
              key={index}
              sx={{
                p: 2,
                bgcolor: alpha(theme.palette.background.paper, 0.5),
                borderRadius: 1,
                border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
              }}
            >
              <Skeleton
                {...skeletonBaseProps}
                variant="rectangular"
                height={120}
                sx={{ mb: 2 }}
              />
              <Skeleton
                {...skeletonBaseProps}
                variant="text"
                width="70%"
                sx={{ mb: 1 }}
              />
              <Skeleton
                {...skeletonBaseProps}
                variant="text"
                width="50%"
              />
            </Box>
          ))}
        </Box>
      </Box>
    );
  }

  // Upload page skeleton - for resume upload workflow
  if (variant === 'upload') {
    return (
      <Box sx={{ width: '100%', p: 3 }}>
        {/* Page Header Skeleton */}
        <Skeleton
          {...skeletonBaseProps}
          variant="text"
          width="40%"
          height={48}
          sx={{ mb: 1 }}
        />
        <Skeleton
          {...skeletonBaseProps}
          variant="text"
          width="70%"
          height={24}
          sx={{ mb: 1 }}
        />
        <Skeleton
          {...skeletonBaseProps}
          variant="text"
          width="50%"
          height={20}
          sx={{ mb: 3 }}
        />

        {/* Upload Area Skeleton */}
        <Box
          sx={{
            p: 4,
            mt: 3,
            border: '2px dashed',
            borderColor: 'divider',
            borderRadius: 1,
            bgcolor: 'background.paper',
          }}
        >
          {/* Upload Icon Skeleton */}
          <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
            <Skeleton
              {...skeletonBaseProps}
              variant="circular"
              width={64}
              height={64}
            />
          </Box>

          {/* Title Skeleton */}
          <Skeleton
            {...skeletonBaseProps}
            variant="text"
            width="40%"
            sx={{ mx: 'auto', mb: 1 }}
            height={32}
          />

          {/* Subtitle Skeleton */}
          <Skeleton
            {...skeletonBaseProps}
            variant="text"
            width="60%"
            sx={{ mx: 'auto', mb: 2 }}
            height={20}
          />

          {/* Chips Skeleton */}
          <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center', mb: 3 }}>
            <Skeleton {...skeletonBaseProps} variant="rectangular" width={60} height={32} />
            <Skeleton {...skeletonBaseProps} variant="rectangular" width={60} height={32} />
            <Skeleton {...skeletonBaseProps} variant="rectangular" width={100} height={32} />
          </Box>

          {/* Button Skeleton */}
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
            <Skeleton {...skeletonBaseProps} variant="rectangular" width={160} height={40} />
          </Box>
        </Box>

        {/* Instructions Section Skeleton */}
        <Box
          sx={{
            p: 3,
            mt: 3,
            bgcolor: 'action.hover',
            borderRadius: 1,
          }}
        >
          <Skeleton
            {...skeletonBaseProps}
            variant="text"
            width="30%"
            height={28}
            sx={{ mb: 2 }}
          />
          <Skeleton
            {...skeletonBaseProps}
            variant="text"
            width="95%"
            height={20}
            sx={{ mb: 1 }}
          />
          <Skeleton
            {...skeletonBaseProps}
            variant="text"
            width="95%"
            height={20}
            sx={{ mb: 1 }}
          />
          <Skeleton
            {...skeletonBaseProps}
            variant="text"
            width="80%"
            height={20}
          />
        </Box>
      </Box>
    );
  }

  // Analysis results skeleton - for resume analysis workflow
  if (variant === 'analysis') {
    return (
      <Box sx={{ width: '100%', p: 3 }}>
        {/* Page Header */}
        <Box sx={{ mb: 3 }}>
          <Skeleton
            {...skeletonBaseProps}
            variant="text"
            width="30%"
            height={40}
            sx={{ mb: 1 }}
          />
          <Skeleton
            {...skeletonBaseProps}
            variant="text"
            width="50%"
            height={20}
          />
        </Box>

        {/* Tabs Skeleton */}
        <Box sx={{ display: 'flex', gap: 2, mb: 3, borderBottom: `1px solid ${theme.palette.divider}`, pb: 2 }}>
          <Skeleton {...skeletonBaseProps} variant="rectangular" width={100} height={32} />
          <Skeleton {...skeletonBaseProps} variant="rectangular" width={140} height={32} />
        </Box>

        {/* Analysis Sections */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {/* Error Detection Section */}
          <Box
            sx={{
              p: 2,
              bgcolor: alpha(theme.palette.background.paper, 0.5),
              borderRadius: 1,
              border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
            }}
          >
            <Skeleton
              {...skeletonBaseProps}
              variant="text"
              width="25%"
              height={28}
              sx={{ mb: 2 }}
            />
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {[1, 2, 3].map((item) => (
                <Box
                  key={item}
                  sx={{
                    p: 2,
                    bgcolor: 'background.paper',
                    borderRadius: 1,
                    display: 'flex',
                    gap: 2,
                  }}
                >
                  <Skeleton {...skeletonBaseProps} variant="circular" width={24} height={24} />
                  <Box sx={{ flex: 1 }}>
                    <Skeleton
                      {...skeletonBaseProps}
                      variant="text"
                      width="70%"
                      sx={{ mb: 1 }}
                    />
                    <Skeleton {...skeletonBaseProps} variant="text" width="90%" />
                  </Box>
                </Box>
              ))}
            </Box>
          </Box>

          {/* Skills Section */}
          <Box
            sx={{
              p: 2,
              bgcolor: alpha(theme.palette.background.paper, 0.5),
              borderRadius: 1,
              border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
            }}
          >
            <Skeleton
              {...skeletonBaseProps}
              variant="text"
              width="20%"
              height={28}
              sx={{ mb: 2 }}
            />
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {Array.from({ length: 8 }).map((_, index) => (
                <Skeleton
                  key={index}
                  {...skeletonBaseProps}
                  variant="rectangular"
                  width={60 + Math.random() * 40}
                  height={28}
                />
              ))}
            </Box>
          </Box>

          {/* Experience Section */}
          <Box
            sx={{
              p: 2,
              bgcolor: alpha(theme.palette.background.paper, 0.5),
              borderRadius: 1,
              border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
            }}
          >
            <Skeleton
              {...skeletonBaseProps}
              variant="text"
              width="30%"
              height={28}
              sx={{ mb: 2 }}
            />
            <Skeleton
              {...skeletonBaseProps}
              variant="rectangular"
              width="100%"
              height={80}
              sx={{ borderRadius: 1 }}
            />
          </Box>
        </Box>
      </Box>
    );
  }

  // Vacancy details skeleton - for vacancy details page
  if (variant === 'vacancy-details') {
    return (
      <Box sx={{ width: '100%', p: 3 }}>
        {/* Back Button Skeleton */}
        <Skeleton
          {...skeletonBaseProps}
          variant="rectangular"
          width={100}
          height={36}
          sx={{ mb: 2 }}
        />

        {/* Header Paper */}
        <Box
          sx={{
            p: 4,
            mb: 3,
            bgcolor: 'background.paper',
            borderRadius: 1,
            boxShadow: 1,
          }}
        >
          {/* Title and Actions */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
            <Box sx={{ flex: 1 }}>
              <Skeleton
                {...skeletonBaseProps}
                variant="text"
                width="60%"
                height={36}
                sx={{ mb: 1 }}
              />
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Skeleton {...skeletonBaseProps} variant="rectangular" width={100} height={24} />
                <Skeleton {...skeletonBaseProps} variant="rectangular" width={90} height={24} />
              </Box>
            </Box>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Skeleton {...skeletonBaseProps} variant="rectangular" width={80} height={36} />
              <Skeleton {...skeletonBaseProps} variant="rectangular" width={80} height={36} />
            </Box>
          </Box>

          {/* Details Grid */}
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '2fr 1fr' }, gap: 3 }}>
            {/* Description */}
            <Box>
              <Skeleton
                {...skeletonBaseProps}
                variant="text"
                width="30%"
                height={24}
                sx={{ mb: 1 }}
              />
              <Skeleton
                {...skeletonBaseProps}
                variant="text"
                width="100%"
                sx={{ mb: 0.5 }}
              />
              <Skeleton
                {...skeletonBaseProps}
                variant="text"
                width="100%"
                sx={{ mb: 0.5 }}
              />
              <Skeleton
                {...skeletonBaseProps}
                variant="text"
                width="80%"
              />
            </Box>

            {/* Sidebar */}
            <Box>
              <Skeleton
                {...skeletonBaseProps}
                variant="text"
                width="40%"
                height={24}
                sx={{ mb: 1 }}
              />
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
                <Skeleton {...skeletonBaseProps} variant="rectangular" width={70} height={28} />
                <Skeleton {...skeletonBaseProps} variant="rectangular" width={80} height={28} />
                <Skeleton {...skeletonBaseProps} variant="rectangular" width={65} height={28} />
              </Box>

              <Skeleton
                {...skeletonBaseProps}
                variant="text"
                width="50%"
                height={24}
                sx={{ mb: 1, mt: 2 }}
              />
              <Skeleton
                {...skeletonBaseProps}
                variant="rectangular"
                width="100%"
                height={56}
                sx={{ borderRadius: 1 }}
              />
            </Box>
          </Box>
        </Box>
      </Box>
    );
  }

  // Dashboard skeleton - for recruiter dashboard
  if (variant === 'dashboard') {
    return (
      <Box sx={{ width: '100%', p: 3 }}>
        {/* Page Header */}
        <Box sx={{ mb: 4 }}>
          <Skeleton
            {...skeletonBaseProps}
            variant="text"
            width="40%"
            height={40}
            sx={{ mb: 1 }}
          />
          <Skeleton
            {...skeletonBaseProps}
            variant="text"
            width="60%"
            height={20}
          />
        </Box>

        {/* Stats Cards */}
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: {
              xs: '1fr',
              sm: 'repeat(2, 1fr)',
              md: 'repeat(4, 1fr)',
            },
            gap: 3,
            mb: 4,
          }}
        >
          {Array.from({ length: 4 }).map((_, index) => (
            <Box
              key={index}
              sx={{
                p: 2,
                bgcolor: 'background.paper',
                borderRadius: 1,
                boxShadow: 1,
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Skeleton {...skeletonBaseProps} variant="circular" width={24} height={24} sx={{ mr: 1 }} />
                <Skeleton {...skeletonBaseProps} variant="text" width="70%" height={20} />
              </Box>
              <Skeleton {...skeletonBaseProps} variant="text" width="40%" height={32} sx={{ mb: 0.5 }} />
              <Skeleton {...skeletonBaseProps} variant="text" width="60%" height={16} />
            </Box>
          ))}
        </Box>

        {/* Quick Actions */}
        <Skeleton
          {...skeletonBaseProps}
          variant="text"
          width="30%"
          height={24}
          sx={{ mb: 2 }}
        />
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: {
              xs: '1fr',
              sm: 'repeat(2, 1fr)',
              md: 'repeat(4, 1fr)',
            },
            gap: 3,
          }}
        >
          {Array.from({ length: 4 }).map((_, index) => (
            <Box
              key={index}
              sx={{
                p: 2,
                bgcolor: 'background.paper',
                borderRadius: 1,
                boxShadow: 1,
                minHeight: 120,
              }}
            >
              <Skeleton {...skeletonBaseProps} variant="circular" width={40} height={40} sx={{ mb: 2 }} />
              <Skeleton
                {...skeletonBaseProps}
                variant="text"
                width="70%"
                sx={{ mb: 1 }}
              />
              <Skeleton {...skeletonBaseProps} variant="text" width="90%" height={16} />
            </Box>
          ))}
        </Box>
      </Box>
    );
  }

  // Candidate search skeleton - for candidate search workflow
  if (variant === 'candidate-search') {
    return (
      <Box sx={{ width: '100%', p: 3 }}>
        {/* Page Header */}
        <Box sx={{ mb: 3 }}>
          <Skeleton
            {...skeletonBaseProps}
            variant="text"
            width="35%"
            height={40}
            sx={{ mb: 1 }}
          />
          <Skeleton
            {...skeletonBaseProps}
            variant="text"
            width="65%"
            height={20}
          />
        </Box>

        {/* Search Filters */}
        <Box
          sx={{
            p: 2,
            mb: 3,
            bgcolor: 'background.paper',
            borderRadius: 1,
            boxShadow: 1,
          }}
        >
          {/* Search Input */}
          <Skeleton
            {...skeletonBaseProps}
            variant="rectangular"
            width="100%"
            height={56}
            sx={{ borderRadius: 1, mb: 2 }}
          />

          {/* Filters Row */}
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
            <Skeleton {...skeletonBaseProps} variant="text" width="15%" height={20} />
            <Skeleton {...skeletonBaseProps} variant="rectangular" width="30%" height={40} />

            <Skeleton {...skeletonBaseProps} variant="text" width="20%" height={20} />
            <Skeleton {...skeletonBaseProps} variant="rectangular" width={100} height={32} />

            <Skeleton {...skeletonBaseProps} variant="rectangular" width={120} height={40} sx={{ ml: 'auto' }} />
          </Box>
        </Box>

        {/* Candidate Cards */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {Array.from({ length: count }).map((_, index) => (
            <Box
              key={index}
              sx={{
                p: 2,
                bgcolor: 'background.paper',
                borderRadius: 1,
                boxShadow: 1,
                display: 'flex',
                gap: 2,
                alignItems: 'center',
              }}
            >
              {/* Avatar/Icon */}
              <Skeleton {...skeletonBaseProps} variant="circular" width={56} height={56} />

              {/* Candidate Info */}
              <Box sx={{ flex: 1 }}>
                <Skeleton
                  {...skeletonBaseProps}
                  variant="text"
                  width="40%"
                  height={24}
                  sx={{ mb: 0.5 }}
                />
                <Skeleton
                  {...skeletonBaseProps}
                  variant="text"
                  width="60%"
                  height={20}
                  sx={{ mb: 1 }}
                />
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  <Skeleton {...skeletonBaseProps} variant="rectangular" width={60} height={24} />
                  <Skeleton {...skeletonBaseProps} variant="rectangular" width={75} height={24} />
                  <Skeleton {...skeletonBaseProps} variant="rectangular" width={55} height={24} />
                </Box>
              </Box>

              {/* Match Score */}
              <Box sx={{ textAlign: 'right' }}>
                <Skeleton
                  {...skeletonBaseProps}
                  variant="text"
                  width={60}
                  height={32}
                  sx={{ mb: 0.5 }}
                />
                <Skeleton
                  {...skeletonBaseProps}
                  variant="text"
                  width={80}
                  height={20}
                />
              </Box>

              {/* Actions */}
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Skeleton {...skeletonBaseProps} variant="rectangular" width={36} height={36} />
                <Skeleton {...skeletonBaseProps} variant="rectangular" width={36} height={36} />
              </Box>
            </Box>
          ))}
        </Box>
      </Box>
    );
  }

  // Fallback to spinner
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        p: 4,
      }}
    >
      <CircularProgress size={size} />
    </Box>
  );
};

export default LoadingSpinner;
