import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  CalendarConnectionCreate,
  CalendarConnectionUpdate,
  CalendarConnectionResponse,
  CalendarConnectionListResponse,
  AvailabilityCheckRequest,
  AvailabilityCheckResponse,
  ApiError,
} from '@/types/api'; posed

export interface CalendarConnectionFilters {
  recruiter_id?: string;
  provider?: string;
  status?: string;
}

const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
};

export class CalendarClient {
  private client: AxiosInstance;

  constructor(config: Partial<typeof DEFAULT_CONFIG> = {}) {
    const finalConfig = { ...DEFAULT_CONFIG, ...config };
    this.client = axios.create(finalConfig);
    this.client.interceptors.response.use(
      (response) => response,
      (error) => Promise.reject(this.transformError(error))
    );
  }

  private transformError(error: unknown): ApiError {
    const axiosError = error as AxiosError<{ detail?: string }>;
    if (!axiosError.response) {
      if (axiosError.code === 'ECONNABORTED') {
        return { detail: 'Request timeout. Please check your connection and try again.', status: 408 };
      }
      return { detail: 'Network error. Please check your connection and try again.', status: 0 };
    }
    const status = axiosError.response.status;
    const data = axiosError.response.data;
    if (data?.detail) {
      return { detail: data.detail, status };
    }
    const defaultMessages: Record<number, string> = {
      400: 'Invalid request. Please check your input.',
      401: 'Unauthorized. Please log in.',
      403: 'Forbidden. You do not have permission.',
      404: 'Resource not found.',
      409: 'A conflict occurred with this calendar connection.',
      422: 'Validation error. Please check your input.',
      429: 'Too many requests. Please try again later.',
      500: 'Server error. Please try again later.',
      502: 'Bad gateway. Please try again later.',
      503: 'Service unavailable. Please try again later.',
    };
    return { detail: data?.detail || defaultMessages[status] || 'An unexpected error occurred.', status };
  }

  async createConnection(request: CalendarConnectionCreate): Promise<CalendarConnectionResponse> {
    try {
      const response: AxiosResponse<CalendarConnectionResponse> = await this.client.post(
        '/api/calendar/connections',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  async listConnections(filters?: CalendarConnectionFilters): Promise<CalendarConnectionListResponse> {
    try {
      const params: Record<string, string | number> = {};
      if (filters?.recruiter_id) params.recruiter_id = filters.recruiter_id;
      if (filters?.provider) params.provider = filters.provider;
      if (filters?.status) params.status = filters.status;
      const response: AxiosResponse<CalendarConnectionListResponse> = await this.client.get(
        '/api/calendar/connections',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  async getConnection(connectionId: string): Promise<CalendarConnectionResponse> {
    try {
      const response: AxiosResponse<CalendarConnectionResponse> = await this.client.get(
        `/api/calendar/connections/${connectionId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  async updateConnection(
    connectionId: string,
    request: CalendarConnectionUpdate
  ): Promise<CalendarConnectionResponse> {
    try {
      const response: AxiosResponse<CalendarConnectionResponse> = await this.client.put(
        `/api/calendar/connections/${connectionId}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  async deleteConnection(connectionId: string): Promise<void> {
    try {
      await this.client.delete(`/api/calendar/connections/${connectionId}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  async checkAvailability(request: AvailabilityCheckRequest): Promise<AvailabilityCheckResponse[]> {
    try {
      const response: AxiosResponse<AvailabilityCheckResponse[]> = await this.client.post(
        '/api/calendar/check-availability',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  getAxiosInstance(): AxiosInstance {
    return this.client;
  }
}

export const calendarClient = new CalendarClient();

export default CalendarClient;
