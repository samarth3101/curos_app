import { api } from '../lib/api';
import type { components } from '@curos/types';

type OrganizationCreate = components['schemas']['OrganizationCreate'];
type OrganizationResponse = components['schemas']['OrganizationResponse'];

export const organizationsService = {
  // GET /organizations/me — returns orgs the current user is a member of
  list: async () => {
    const response = await api.get<OrganizationResponse[]>('/organizations/me');
    return response.data;
  },

  create: async (data: OrganizationCreate) => {
    const response = await api.post<OrganizationResponse>('/organizations', data);
    return response.data;
  },

  getById: async (id: string) => {
    const response = await api.get<OrganizationResponse>(`/organizations/${id}`);
    return response.data;
  },
};
