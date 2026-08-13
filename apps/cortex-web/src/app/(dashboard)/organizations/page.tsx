"use client";

import { useCallback, useEffect, useState } from 'react';
import { useOrgStore } from '@/stores/orgStore';
import { organizationsService } from '@/services/organizations';
import type { components } from '@curos/types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Modal } from '@/components/ui/modal';
import { Badge } from '@/components/ui/badge';
import { Plus } from 'lucide-react';

type Organization = components['schemas']['OrganizationResponse'];

export default function OrganizationsPage() {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const { activeOrganization, setActiveOrganization } = useOrgStore();
  
  // Create Form State
  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [type, setType] = useState('university');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchOrganizations = useCallback(async () => {
    try {
      setLoading(true);
      const data = await organizationsService.list();
      setOrganizations(data);
    } catch (error) {
      console.error('Failed to fetch organizations:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchOrganizations();
  }, [fetchOrganizations]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const newOrg = await organizationsService.create({ name, slug: slug || undefined, type });
      setOrganizations([...organizations, newOrg]);
      setActiveOrganization(newOrg);
      setIsCreateModalOpen(false);
      setName('');
      setSlug('');
    } catch (error) {
      const axiosError = error as { response?: { data?: { detail?: string; error?: { message?: string } } } };
      console.error('Failed to create organization:', error);
      const msg = axiosError.response?.data?.detail || axiosError.response?.data?.error?.message || 'Failed to create organization';
      alert(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-gray-900">Organizations</h2>
          <p className="text-gray-500">Manage your institutional tenants.</p>
        </div>
        <Button onClick={() => setIsCreateModalOpen(true)}>
          <Plus className="mr-2 h-4 w-4" /> Create Organization
        </Button>
      </div>

      <div className="rounded-md border bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Slug</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-8 text-gray-500">Loading organizations...</TableCell>
              </TableRow>
            ) : organizations.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-8 text-gray-500">No organizations found.</TableCell>
              </TableRow>
            ) : (
              organizations.map((org) => (
                <TableRow key={org.id} data-state={activeOrganization?.id === org.id ? 'selected' : undefined}>
                  <TableCell className="font-medium">
                    {org.name}
                    {activeOrganization?.id === org.id && (
                      <Badge variant="success" className="ml-2">Active</Badge>
                    )}
                  </TableCell>
                  <TableCell>{org.slug}</TableCell>
                  <TableCell className="capitalize">{org.type}</TableCell>
                  <TableCell>
                    <Badge variant={org.status === 'ACTIVE' ? 'success' : 'secondary'}>
                      {org.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button 
                      variant={activeOrganization?.id === org.id ? "outline" : "default"} 
                      size="sm"
                      onClick={() => setActiveOrganization(org)}
                      disabled={activeOrganization?.id === org.id}
                    >
                      {activeOrganization?.id === org.id ? 'Current' : 'Select'}
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Create Organization"
      >
        <form onSubmit={handleCreate} className="space-y-4 pt-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Name</label>
            <Input required value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Stanford University" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Slug (Optional)</label>
            <Input value={slug} onChange={e => setSlug(e.target.value)} placeholder="e.g. stanford" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Type</label>
            <select 
              className="flex h-9 w-full rounded-md border border-gray-300 bg-white px-3 py-1 text-sm text-gray-900 shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
              value={type} 
              onChange={e => setType(e.target.value)}
            >
              <option value="corporate">Corporate</option>
              <option value="university">University</option>
              <option value="hospital">Hospital</option>
              <option value="nonprofit">Non-Profit</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div className="flex justify-end space-x-2 pt-4">
            <Button type="button" variant="outline" onClick={() => setIsCreateModalOpen(false)}>Cancel</Button>
            <Button type="submit" disabled={isSubmitting}>{isSubmitting ? 'Creating...' : 'Create'}</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
