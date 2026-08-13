import { api } from '../lib/api';
import type { components } from '@curos/types';

type RoleResponse = components['schemas']['RoleResponse'];

export const rolesService = {
  list: async (orgId: string) => {
    const response = await api.get<RoleResponse[]>(`/organizations/${orgId}/roles`);
    return response.data;
  },

  create: async (orgId: string, name: string, description?: string) => {
    const response = await api.post<RoleResponse>(`/organizations/${orgId}/roles`, { name, description });
    return response.data;
  },

  // Assign a role to a member: POST /organizations/{orgId}/members/{userId}/role
  assignRole: async (orgId: string, userId: string, roleId: string) => {
    await api.post(`/organizations/${orgId}/members/${userId}/role`, { role_id: roleId });
  },
};
