import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { components } from '@curos/types';

type Organization = components['schemas']['OrganizationResponse'];

interface OrgState {
  activeOrganization: Organization | null;
  organizations: Organization[];
  setActiveOrganization: (org: Organization) => void;
  setOrganizations: (orgs: Organization[]) => void;
  clearActiveOrganization: () => void;
}

export const useOrgStore = create<OrgState>()(
  persist(
    (set) => ({
      activeOrganization: null,
      organizations: [],
      setActiveOrganization: (org) => set({ activeOrganization: org }),
      setOrganizations: (orgs) => {
        set((state) => {
          // Keep active org in sync if it's in the new list; otherwise pick first
          const newActive = orgs.find((o) => o.id === state.activeOrganization?.id) ?? orgs[0] ?? null;
          return { organizations: orgs, activeOrganization: newActive };
        });
      },
      clearActiveOrganization: () => set({ activeOrganization: null, organizations: [] }),
    }),
    {
      name: 'cortex-org',
    }
  )
);
