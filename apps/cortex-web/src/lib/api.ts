/**
 * Axios instance for communicating with the cortex-api backend.
 *
 * - baseURL loaded from environment (NEXT_PUBLIC_API_URL)
 * - Automatic Authorization header injection from stored token
 * - Response interceptor for structured error handling
 */

import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 10_000,
});

// ---- Request interceptor: inject access token ----
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// ---- Response interceptor: structured error handling ----
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ error?: { code: string; message: string } }>) => {
    const cortexError = error.response?.data?.error;
    if (cortexError) {
      // Re-throw with the structured error from the backend
      return Promise.reject(
        Object.assign(new Error(cortexError.message), {
          code: cortexError.code,
          status: error.response?.status,
        })
      );
    }
    return Promise.reject(error);
  }
);

export default api;
