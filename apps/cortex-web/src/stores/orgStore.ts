import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { components } from '@curos/types';

type Organization = components['schemas']['OrganizationResponse'];

interface OrgState {
  activeOrganization: Organization | null;
  setActiveOrganization: (org: Organization) => void;
  clearActiveOrganization: () => void;
}

export const useOrgStore = create<OrgState>()(
  persist(
    (set) => ({
      activeOrganization: null,
      setActiveOrganization: (org) => set({ activeOrganization: org }),
      clearActiveOrganization: () => set({ activeOrganization: null }),
    }),
    {
      name: 'cortex-org',
    }
  )
);
