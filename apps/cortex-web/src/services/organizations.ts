import { api } from '../lib/api';
import type { components } from '@curos/types';

type OrganizationCreate = components['schemas']['OrganizationCreate'];
type OrganizationResponse = components['schemas']['OrganizationResponse'];

export interface MemberWithRoles {
  id: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  status: string;
  membership_id: string;
  roles: string[];
  joined_at?: string | null;
}

export interface OrgStats {
  total_members: number;
  total_events: number;
  upcoming_events: number;
  pending_approvals: number;
  total_registrations: number;
  total_attendance: number;
}

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

  // GET /organizations/{id}/members — returns members with roles
  listMembers: async (orgId: string) => {
    const response = await api.get<MemberWithRoles[]>(`/organizations/${orgId}/members`);
    return response.data;
  },

  // POST /organizations/{id}/members — Add Member (not invite)
  addMember: async (orgId: string, email: string, roleId: string) => {
    const response = await api.post<MemberWithRoles>(`/organizations/${orgId}/members`, {
      email,
      role_id: roleId,
    });
    return response.data;
  },

  // GET /organizations/{id}/stats
  getStats: async (orgId: string) => {
    const response = await api.get<OrgStats>(`/organizations/${orgId}/stats`);
    return response.data;
  },

  // GET /organizations/{id}/roles
  listRoles: async (orgId: string) => {
    const response = await api.get<Array<{ id: string; name: string; description: string | null }>>(`/organizations/${orgId}/roles`);
    return response.data;
  },
};
