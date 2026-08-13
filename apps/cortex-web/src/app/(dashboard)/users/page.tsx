"use client";

import { useEffect, useState } from 'react';
import { useOrgStore } from '@/stores/orgStore';
import { usersService, type UserResponse } from '@/services/users';
import { rolesService } from '@/services/roles';
import type { components } from '@curos/types';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Modal } from '@/components/ui/modal';
import { Badge } from '@/components/ui/badge';
import { Shield } from 'lucide-react';

type RoleResponse = components['schemas']['RoleResponse'];

export default function UsersPage() {
  const { activeOrganization } = useOrgStore();
  const [users, setUsers] = useState<UserResponse[]>([]);
  const [roles, setRoles] = useState<RoleResponse[]>([]);
  const [loading, setLoading] = useState(true);

  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState('');
  const [selectedRoleId, setSelectedRoleId] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [assignError, setAssignError] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      if (!activeOrganization) return;
      try {
        setLoading(true);
        const [usersData, rolesData] = await Promise.all([
          usersService.listOrganizationMembers(activeOrganization.id),
          rolesService.list(activeOrganization.id),
        ]);
        setUsers(usersData);
        setRoles(rolesData);
      } catch (error) {
        console.error('Failed to fetch users or roles:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [activeOrganization]);

  const handleAssignRole = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeOrganization) return;
    setIsSubmitting(true);
    setAssignError('');
    try {
      await rolesService.assignRole(activeOrganization.id, selectedUserId, selectedRoleId);
      alert('Role assigned successfully!');
      setIsAssignModalOpen(false);
      setSelectedUserId('');
      setSelectedRoleId('');
    } catch (error) {
      const axiosError = error as { response?: { data?: { detail?: string; error?: { message?: string } } } };
      const msg = axiosError.response?.data?.detail || axiosError.response?.data?.error?.message || 'Failed to assign role';
      setAssignError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!activeOrganization) {
    return (
      <div className="flex flex-col items-center justify-center h-[50vh] text-center">
        <h2 className="text-xl font-semibold mb-2 text-gray-900">No Active Organization</h2>
        <p className="text-gray-500 mb-4">Please select an organization from the Organizations tab first.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-gray-900">Users & Roles</h2>
          <p className="text-gray-500">Members of {activeOrganization.name}.</p>
        </div>
        <Button onClick={() => { setIsAssignModalOpen(true); setAssignError(''); }}>
          <Shield className="mr-2 h-4 w-4" /> Assign Role
        </Button>
      </div>

      {roles.length === 0 && (
        <div className="rounded-md bg-amber-50 border border-amber-200 px-4 py-3 text-sm text-amber-800">
          <strong>No roles found.</strong> Create roles from the organization settings before assigning them to members.
        </div>
      )}

      <div className="rounded-md border bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Role</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center py-8 text-gray-500">Loading members...</TableCell>
              </TableRow>
            ) : users.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center py-8 text-gray-500">No members found.</TableCell>
              </TableRow>
            ) : (
              users.map((user) => (
                <TableRow key={user.id}>
                  <TableCell className="font-medium text-gray-900">{user.first_name} {user.last_name}</TableCell>
                  <TableCell className="text-gray-700">{user.email}</TableCell>
                  <TableCell className="text-gray-600 capitalize">{user.role}</TableCell>
                  <TableCell>
                    <Badge variant="success">active</Badge>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      <Modal isOpen={isAssignModalOpen} onClose={() => setIsAssignModalOpen(false)} title="Assign Role to Member">
        <form onSubmit={handleAssignRole} className="space-y-4 pt-4">
          {assignError && (
            <div className="rounded-md bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">
              {assignError}
            </div>
          )}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">User</label>
            <select
              className="flex h-9 w-full rounded-md border border-gray-300 bg-white px-3 py-1 text-sm text-gray-900 shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
              required
              value={selectedUserId}
              onChange={e => setSelectedUserId(e.target.value)}
            >
              <option value="" disabled>Select a user</option>
              {users.map(u => (
                <option key={u.id} value={u.id}>{u.first_name} {u.last_name} ({u.email})</option>
              ))}
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">Role</label>
            {roles.length === 0 ? (
              <p className="text-sm text-amber-600">No roles available. Create roles first.</p>
            ) : (
              <select
                className="flex h-9 w-full rounded-md border border-gray-300 bg-white px-3 py-1 text-sm text-gray-900 shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                required
                value={selectedRoleId}
                onChange={e => setSelectedRoleId(e.target.value)}
              >
                <option value="" disabled>Select a role</option>
                {roles.map(r => (
                  <option key={r.id} value={r.id}>{r.name}</option>
                ))}
              </select>
            )}
          </div>
          <div className="flex justify-end space-x-2 pt-4 border-t">
            <Button type="button" variant="outline" onClick={() => setIsAssignModalOpen(false)}>Cancel</Button>
            <Button type="submit" disabled={isSubmitting || !selectedUserId || !selectedRoleId || roles.length === 0}>
              {isSubmitting ? 'Assigning...' : 'Assign Role'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
