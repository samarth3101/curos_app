import { api } from '../lib/api';
import type { components } from '@curos/types';

type PaginatedAuditResponse = components['schemas']['PaginatedAuditResponse'];

export interface AuditFilterParams {
  action?: string;
  actor_id?: string;
  resource_type?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  size?: number;
}

export const auditService = {
  list: async (orgId: string, params?: AuditFilterParams) => {
    const response = await api.get<PaginatedAuditResponse>(`/organizations/${orgId}/audit`, { params });
    return response.data;
  },
};
