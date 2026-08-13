import { api } from '../lib/api';
import type { components } from '@curos/types';

type EventResponse = components['schemas']['EventResponse'];
type EventCreate = components['schemas']['EventCreate'];
type EventRegistrationResponse = components['schemas']['EventRegistrationResponse'];
type EventAttendanceResponse = components['schemas']['EventAttendanceResponse'];
type EventAttendanceCreate = components['schemas']['EventAttendanceCreate'];

// All event endpoints are under /organizations/{orgId}/events
const base = (orgId: string) => `/organizations/${orgId}/events`;

export const eventsService = {
  list: async (orgId: string) => {
    const response = await api.get<EventResponse[]>(base(orgId));
    return response.data;
  },

  create: async (orgId: string, data: EventCreate) => {
    const response = await api.post<EventResponse>(base(orgId), data);
    return response.data;
  },

  getById: async (orgId: string, id: string) => {
    const response = await api.get<EventResponse>(`${base(orgId)}/${id}`);
    return response.data;
  },

  // Lifecycle
  submit: async (orgId: string, id: string) => {
    const response = await api.post(`${base(orgId)}/${id}/submit`);
    return response.data;
  },

  approve: async (orgId: string, id: string) => {
    const response = await api.post(`${base(orgId)}/${id}/approve`);
    return response.data;
  },

  reject: async (orgId: string, id: string) => {
    const response = await api.post(`${base(orgId)}/${id}/reject`);
    return response.data;
  },

  publish: async (orgId: string, id: string) => {
    const response = await api.post(`${base(orgId)}/${id}/publish`);
    return response.data;
  },

  start: async (orgId: string, id: string) => {
    const response = await api.post(`${base(orgId)}/${id}/start`);
    return response.data;
  },

  complete: async (orgId: string, id: string) => {
    const response = await api.post(`${base(orgId)}/${id}/complete`);
    return response.data;
  },

  archive: async (orgId: string, id: string) => {
    const response = await api.post(`${base(orgId)}/${id}/archive`);
    return response.data;
  },

  // Registration
  getRegistrations: async (orgId: string, id: string) => {
    const response = await api.get<EventRegistrationResponse[]>(`${base(orgId)}/${id}/registrations`);
    return response.data;
  },

  register: async (orgId: string, id: string) => {
    const response = await api.post<EventRegistrationResponse>(`${base(orgId)}/${id}/register`);
    return response.data;
  },

  cancelRegistration: async (orgId: string, id: string) => {
    const response = await api.delete(`${base(orgId)}/${id}/register`);
    return response.data;
  },

  // Attendance
  getAttendance: async (orgId: string, id: string) => {
    const response = await api.get<EventAttendanceResponse[]>(`${base(orgId)}/${id}/attendance`);
    return response.data;
  },

  recordAttendance: async (orgId: string, id: string, data: EventAttendanceCreate) => {
    const response = await api.post<EventAttendanceResponse>(`${base(orgId)}/${id}/attendance`, data);
    return response.data;
  },
};
