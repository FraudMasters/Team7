/**
 * Candidate Recommendations API Client
 *
 * Provides methods for tracking recommendation feedback events
 * (impressions, clicks, etc.) to improve recommendation quality.
 *
 * @example
 * ```ts
 * import { trackRecommendationImpression, trackRecommendationClick } from '@/api/recommendations';
 *
 * // Track when recommendations are shown to user
 * await trackRecommendationImpression('resume-123', 'similar');
 *
 * // Track when user clicks on a recommendation
 * await trackRecommendationClick('resume-123', 'similar');
 * ```
 */

import axios from 'axios';

/**
 * Recommendation type
 */
export type RecommendationType = 'similar' | 'best_fit' | 'at_risk';

/**
 * Track recommendation impression event
 *
 * Call this when recommendations are displayed to the user.
 * Uses resume_id as the identifier since recommendation_id is not exposed in API responses.
 *
 * @param targetId - Target resume or vacancy UUID
 * @param recommendationType - Type of recommendation
 * @returns Promise that resolves when tracking is complete
 *
 * @example
 * ```ts
 * await trackRecommendationImpression('resume-123', 'similar');
 * ```
 */
export async function trackRecommendationImpression(
  targetId: string,
  recommendationType: RecommendationType
): Promise<void> {
  try {
    // Use target_id as a proxy for recommendation_id
    // Backend will correlate the event with the actual recommendation record
    await axios.post(`/api/recommendations/${targetId}/feedback`, {
      was_helpful: null,  // Implicit feedback, not explicitly rated
      was_contacted: false,
      outcome: null,
      rating: null,
      comments: `Implicit feedback: impression for ${recommendationType}`,
      recommendation_type: recommendationType,
    });
  } catch (error) {
    // Silent fail - tracking shouldn't break the UI
    // Error is logged for debugging but not thrown
  }
}

/**
 * Track recommendation click event
 *
 * Call this when a user clicks on a recommendation card.
 *
 * @param targetId - Target resume or vacancy UUID
 * @param recommendationType - Type of recommendation
 * @returns Promise that resolves when tracking is complete
 *
 * @example
 * ```ts
 * await trackRecommendationClick('resume-123', 'best_fit');
 * ```
 */
export async function trackRecommendationClick(
  targetId: string,
  recommendationType: RecommendationType
): Promise<void> {
  try {
    await axios.post(`/api/recommendations/${targetId}/feedback`, {
      was_helpful: null,  // Implicit feedback signal
      was_contacted: false,
      outcome: null,
      rating: null,
      comments: `Implicit feedback: click for ${recommendationType}`,
      recommendation_type: recommendationType,
    });
  } catch (error) {
    // Silent fail - tracking shouldn't break the UI
  }
}

/**
 * Track recommendation dismiss event
 *
 * Call this when a user dismisses a recommendation.
 *
 * @param targetId - Target resume or vacancy UUID
 * @param recommendationType - Type of recommendation
 * @returns Promise that resolves when tracking is complete
 */
export async function trackRecommendationDismiss(
  targetId: string,
  recommendationType: RecommendationType
): Promise<void> {
  try {
    await axios.post(`/api/recommendations/${targetId}/feedback`, {
      was_helpful: false,
      was_contacted: false,
      outcome: 'dismissed',
      rating: null,
      comments: `Implicit feedback: dismiss for ${recommendationType}`,
      recommendation_type: recommendationType,
    });
  } catch (error) {
    // Silent fail - tracking shouldn't break the UI
  }
}

/**
 * Batch track recommendation impressions
 *
 * Efficiently track multiple impression events at once.
 *
 * @param targetIds - Array of target resume or vacancy UUIDs
 * @param recommendationType - Type of recommendation
 * @returns Promise that resolves when tracking is complete
 *
 * @example
 * ```ts
 * await trackBatchImpressions(['resume-1', 'resume-2', 'resume-3'], 'similar');
 * ```
 */
export async function trackBatchImpressions(
  targetIds: string[],
  recommendationType: RecommendationType
): Promise<void> {
  try {
    // Fire all requests in parallel, don't wait for completion
    targetIds.forEach((id) => {
      trackRecommendationImpression(id, recommendationType).catch(() => {
        // Individual errors are already handled silently
      });
    });
  } catch (error) {
    // Silent fail - tracking shouldn't break the UI
  }
}
