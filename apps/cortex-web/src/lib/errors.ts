/**
 * Centralized API error normalization.
 * Translates raw Axios errors into human-readable messages.
 */

import { AxiosError } from 'axios';

interface ApiErrorBody {
  error?: {
    code?: string;
    message?: string;
    details?: Array<{ field: string; message: string }>;
  };
  detail?: string | Array<{ loc?: string[]; msg?: string }>;
  message?: string;
}

const STATUS_MESSAGES: Record<number, string> = {
  400: 'Invalid request. Please check your input.',
  401: 'Your session has expired. Please log in again.',
  403: "You don't have permission to perform this action.",
  404: 'The requested resource was not found.',
  409: 'Conflict — this action cannot be completed due to an existing record.',
  422: 'Validation error. Please check the form fields.',
  500: 'Something went wrong on our end. Please try again.',
  502: 'Service unavailable. Please try again shortly.',
  503: 'Service unavailable. Please try again shortly.',
};

/**
 * Extract a human-readable message from any thrown error.
 * Never returns {} or raw stack traces.
 */
export function normalizeApiError(error: unknown): string {
  if (error instanceof AxiosError) {
    const status = error.response?.status;
    const body = error.response?.data as ApiErrorBody | undefined;

    // Try to get the structured error message from our API format
    if (body?.error?.message) {
      return body.error.message;
    }

    // Handle FastAPI validation detail format
    if (body?.detail) {
      if (typeof body.detail === 'string') {
        return body.detail;
      }
      // FastAPI returns an array of validation errors
      if (Array.isArray(body.detail)) {
        return body.detail
          .map((d: { loc?: string[]; msg?: string }) => d.msg || JSON.stringify(d))
          .join('; ');
      }
    }

    if (body?.message && typeof body.message === 'string') {
      return body.message;
    }

    // Fall back to status-based message
    if (status && STATUS_MESSAGES[status]) {
      return STATUS_MESSAGES[status];
    }

    // Network error
    if (!error.response) {
      return 'Unable to connect. Please check your internet connection.';
    }
  }

  // Non-Axios error
  if (error instanceof Error) {
    return error.message || 'An unexpected error occurred.';
  }

  return 'An unexpected error occurred.';
}

/**
 * Check if the error is a specific HTTP status.
 */
export function isHttpError(error: unknown, status: number): boolean {
  return error instanceof AxiosError && error.response?.status === status;
}
