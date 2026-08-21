"use client";

import { useState, useEffect } from 'react';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/authStore';
import { useOrgStore } from '@/stores/orgStore';
import { organizationsService } from '@/services/organizations';
import { normalizeApiError } from '@/lib/errors';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Building2, ArrowRight, CheckCircle } from 'lucide-react';

type OrgType = 'university' | 'company' | 'ngo' | 'government' | 'other';

const ORG_TYPES: { value: OrgType; label: string }[] = [
  { value: 'university', label: 'University / College' },
  { value: 'company', label: 'Company / Startup' },
  { value: 'ngo', label: 'NGO / Non-Profit' },
  { value: 'government', label: 'Government' },
  { value: 'other', label: 'Other' },
];

export default function OnboardingPage() {
  const { user } = useAuthStore();
  const { organizations, activeOrganization, setOrganizations, setActiveOrganization } = useOrgStore();
  const router = useRouter();

  const [loading, setLoading] = useState(true);
  const [name, setName] = useState('');
  const [orgType, setOrgType] = useState<OrgType>('university');
  const [slug, setSlug] = useState('');
  const [error, setError] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    const fetchOrgs = async () => {
      try {
        const orgs = await organizationsService.list();
        setOrganizations(orgs);
        if (orgs.length > 0 && !activeOrganization) {
          setActiveOrganization(orgs[0]);
        }
      } catch {
        // Ignore — user may have no orgs yet
      } finally {
        setLoading(false);
      }
    };
    fetchOrgs();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Auto-generate slug from name
  useEffect(() => {
    if (name) {
      setSlug(name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''));
    }
  }, [name]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setCreating(true);

    try {
      const org = await organizationsService.create({ name, slug: slug || undefined, type: orgType });
      const updatedOrgs = [...organizations, org];
      setOrganizations(updatedOrgs);
      setActiveOrganization(org);
      router.push('/');
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setCreating(false);
    }
  };

  const handleSelectOrg = (orgId: string) => {
    const org = organizations.find((o) => o.id === orgId);
    if (org) {
      setActiveOrganization(org);
      router.push('/');
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="text-gray-400 text-sm">Loading...</div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
      <div className="w-full max-w-lg space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="flex justify-center">
            <Image src="/curos_logo.png" alt="Curos" width={48} height={48} className="h-12 w-auto object-contain" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome{user?.first_name ? `, ${user.first_name}` : ''}!
          </h1>
          <p className="text-gray-500">Get started with Cortex OI</p>
        </div>

        {/* Existing organizations */}
        {organizations.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Your Organizations</CardTitle>
              <CardDescription>Select an organization to continue</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {organizations.map((org) => (
                <button
                  key={org.id}
                  onClick={() => handleSelectOrg(org.id)}
                  className="w-full flex items-center justify-between p-3 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors text-left group"
                >
                  <div className="flex items-center gap-3">
                    <div className="h-9 w-9 rounded-lg bg-blue-100 flex items-center justify-center">
                      <Building2 className="h-5 w-5 text-blue-600" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{org.name}</p>
                      <p className="text-xs text-gray-500 capitalize">{org.type} · {org.slug}</p>
                    </div>
                  </div>
                  {activeOrganization?.id === org.id ? (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  ) : (
                    <ArrowRight className="h-5 w-5 text-gray-400 group-hover:text-blue-600 transition-colors" />
                  )}
                </button>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Create new organization */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">
              {organizations.length === 0 ? 'Create Your Organization' : 'Or Create a New One'}
            </CardTitle>
            <CardDescription>
              {organizations.length === 0
                ? 'Set up your first organization to get started'
                : 'Add another organization to your account'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-4">
              {error && <div className="rounded-md bg-red-50 p-3 text-sm text-red-600">{error}</div>}

              <div className="space-y-2">
                <label className="text-sm font-medium" htmlFor="org-name">Organization Name</label>
                <Input
                  id="org-name"
                  placeholder="e.g. Pune City University"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium" htmlFor="org-type">Type</label>
                <select
                  id="org-type"
                  value={orgType}
                  onChange={(e) => setOrgType(e.target.value as OrgType)}
                  className="w-full h-9 rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs outline-none focus-visible:border-ring"
                >
                  {ORG_TYPES.map((t) => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium" htmlFor="org-slug">
                  Slug <span className="text-gray-400 font-normal">(auto-generated)</span>
                </label>
                <Input
                  id="org-slug"
                  placeholder="pune-city-university"
                  value={slug}
                  onChange={(e) => setSlug(e.target.value)}
                />
                <p className="text-xs text-gray-400">Used in URLs. Lowercase, hyphens only.</p>
              </div>

              <Button type="submit" className="w-full" disabled={creating || !name}>
                {creating ? 'Creating...' : 'Create Organization'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
