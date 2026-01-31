/**
 * Candidate Notes API Client
 *
 * This module provides a client for managing candidate notes and comments,
 * including creating, reading, updating, and deleting collaborative notes.
 *
 * @example
 * ```ts
 * import { candidateNotesClient } from '@/api/candidateNotes';
 *
 * // List all notes for a candidate
 * const notes = await candidateNotesClient.listNotes('resume-123');
 *
 * // Create a new note
 * const newNote = await candidateNotesClient.createNote({
 *   resume_id: 'resume-123',
 *   content: 'Great candidate, strong technical skills',
 *   recruiter_id: 'recruiter-123',
 *   is_private: false
 * });
 *
 * // Update a note
 * const updated = await candidateNotesClient.updateNote('note-id', {
 *   content: 'Updated note content',
 *   is_private: true
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  CandidateNoteCreate,
  CandidateNoteUpdate,
  CandidateNoteResponse,
  CandidateNoteListResponse,
  ApiError,
} from '@/types/api';

/**
 * Default API configuration for candidate notes client
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  timeout: 10000, // 10 seconds
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Candidate Notes API Client class
 *
 * Provides methods for managing candidate notes with proper
 * error handling and type safety.
 */
export class CandidateNotesClient {
  private client: AxiosInstance;

  /**
   * Create a new CandidateNotes client instance
   *
   * @param config - Optional configuration overrides
   */
  constructor(config: Partial<typeof DEFAULT_CONFIG> = {}) {
    const finalConfig = { ...DEFAULT_CONFIG, ...config };

    this.client = axios.create(finalConfig);

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => Promise.reject(this.transformError(error))
    );
  }

  /**
   * Transform Axios error to standardized API error
   *
   * @param error - Axios error
   * @returns Transformed API error
   */
  private transformError(error: unknown): ApiError {
    const axiosError = error as AxiosError<{ detail?: string }>;

    // Network error (no response)
    if (!axiosError.response) {
      if (axiosError.code === 'ECONNABORTED') {
        return {
          detail: 'Request timeout. Please check your connection and try again.',
          status: 408,
        };
      }
      return {
        detail: 'Network error. Please check your connection and try again.',
        status: 0,
      };
    }

    // Server returned error response
    const status = axiosError.response.status;
    const data = axiosError.response.data;

    // Use server's error message if available
    if (data?.detail) {
      return { detail: data.detail, status };
    }

    // Default error messages by status code
    const defaultMessages: Record<number, string> = {
      400: 'Invalid request. Please check your input.',
      401: 'Unauthorized. Please log in.',
      403: 'Forbidden. You do not have permission.',
      404: 'Resource not found.',
      409: 'A conflict occurred with the existing note.',
      422: 'Validation error. Please check your input.',
      429: 'Too many requests. Please try again later.',
      500: 'Server error. Please try again later.',
      502: 'Bad gateway. Please try again later.',
      503: 'Service unavailable. Please try again later.',
    };

    return {
      detail: data?.detail || defaultMessages[status] || 'An unexpected error occurred.',
      status,
    };
  }

  /**
   * Create a candidate note
   *
   * @param request - Create request with note details
   * @returns Created candidate note
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const note = await candidateNotesClient.createNote({
   *   resume_id: 'resume-123',
   *   content: 'Great candidate, strong technical skills',
   *   recruiter_id: 'recruiter-123',
   *   is_private: false
   * });
   * ```
   */
  async createNote(request: CandidateNoteCreate): Promise<CandidateNoteResponse> {
    try {
      const response: AxiosResponse<CandidateNoteResponse> = await this.client.post(
        '/api/candidate-notes/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List candidate notes with optional filters
   *
   * @param resumeId - Optional resume ID filter
   * @param isPrivate - Optional private status filter
   * @param recruiterId - Optional recruiter (author) ID filter
   * @returns List of candidate notes
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * // Get all notes for a candidate
   * const notes = await candidateNotesClient.listNotes('resume-123');
   *
   * // Get only public notes
   * const publicNotes = await candidateNotesClient.listNotes('resume-123', false);
   *
   * // Get all notes by a specific recruiter
   * const myNotes = await candidateNotesClient.listNotes(undefined, undefined, 'recruiter-123');
   * ```
   */
  async listNotes(
    resumeId?: string,
    isPrivate?: boolean,
    recruiterId?: string
  ): Promise<CandidateNoteListResponse> {
    try {
      const params: Record<string, string | boolean> = {};
      if (resumeId) params.resume_id = resumeId;
      if (isPrivate !== undefined) params.is_private = isPrivate;
      if (recruiterId) params.recruiter_id = recruiterId;

      const response: AxiosResponse<CandidateNoteListResponse> = await this.client.get(
        '/api/candidate-notes/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific candidate note by ID
   *
   * @param noteId - Candidate note ID
   * @returns Candidate note details
   * @throws ApiError if not found
   *
   * @example
   * ```ts
   * const note = await candidateNotesClient.getNote('note-uuid');
   * ```
   */
  async getNote(noteId: string): Promise<CandidateNoteResponse> {
    try {
      const response: AxiosResponse<CandidateNoteResponse> = await this.client.get(
        `/api/candidate-notes/${noteId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update a candidate note
   *
   * @param noteId - Candidate note ID
   * @param request - Update request with fields to modify
   * @returns Updated candidate note
   * @throws ApiError if update fails
   *
   * @example
   * ```ts
   * const updated = await candidateNotesClient.updateNote('note-uuid', {
   *   content: 'Updated note content',
   *   is_private: true
   * });
   * ```
   */
  async updateNote(
    noteId: string,
    request: CandidateNoteUpdate
  ): Promise<CandidateNoteResponse> {
    try {
      const response: AxiosResponse<CandidateNoteResponse> = await this.client.put(
        `/api/candidate-notes/${noteId}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete a candidate note
   *
   * @param noteId - Candidate note ID
   * @throws ApiError if deletion fails
   *
   * @example
   * ```ts
   * await candidateNotesClient.deleteNote('note-uuid');
   * ```
   */
  async deleteNote(noteId: string): Promise<void> {
    try {
      await this.client.delete(`/api/candidate-notes/${noteId}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get the underlying Axios instance
   *
   * This is useful for making custom requests not covered by the convenience methods.
   *
   * @returns Axios instance
   */
  getAxiosInstance(): AxiosInstance {
    return this.client;
  }
}

/**
 * Default candidate notes client instance
 *
 * Use this singleton instance for all candidate notes calls.
 */
export const candidateNotesClient = new CandidateNotesClient();

/**
 * Export candidate notes client class for custom instances
 */
export default CandidateNotesClient;
