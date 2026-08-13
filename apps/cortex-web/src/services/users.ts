import { api } from '../lib/api';
import type { components } from '@curos/types';

// For missing types that we might discover as gaps
export type UserResponse = components['schemas']['UserResponse'];

export const usersService = {
  // Members of an organization
  listOrganizationMembers: async (orgId: string) => {
    const response = await api.get<UserResponse[]>(`/organizations/${orgId}/members`);
    return response.data;
  },
};
