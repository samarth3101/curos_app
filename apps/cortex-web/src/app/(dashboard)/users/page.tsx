"use client";

import { useCallback, useEffect, useState } from 'react';
import { useOrgStore } from '@/stores/orgStore';
import { organizationsService, type MemberWithRoles } from '@/services/organizations';
import { rolesService } from '@/services/roles';
import { normalizeApiError } from '@/lib/errors';
import type { components } from '@curos/types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Modal } from '@/components/ui/modal';
import { Badge } from '@/components/ui/badge';
import { UserPlus, Shield, Users, AlertCircle } from 'lucide-react';

type RoleResponse = components['schemas']['RoleResponse'];

export default function UsersPage() {
  const { activeOrganization } = useOrgStore();
  const [members, setMembers] = useState<MemberWithRoles[]>([]);
  const [roles, setRoles] = useState<RoleResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Add Member modal
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [addEmail, setAddEmail] = useState('');
  const [addRoleId, setAddRoleId] = useState('');
  const [addLoading, setAddLoading] = useState(false);
  const [addError, setAddError] = useState('');

  // Assign Role modal
  const [assignModalOpen, setAssignModalOpen] = useState(false);
  const [assignMemberId, setAssignMemberId] = useState('');
  const [assignRoleId, setAssignRoleId] = useState('');
  const [assignLoading, setAssignLoading] = useState(false);
  const [assignError, setAssignError] = useState('');

  const fetchData = useCallback(async () => {
    if (!activeOrganization) return;
    setLoading(true);
    setError('');
    try {
      const [membersData, rolesData] = await Promise.all([
        organizationsService.listMembers(activeOrganization.id),
        rolesService.list(activeOrganization.id),
      ]);
      setMembers(membersData);
      setRoles(rolesData);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }, [activeOrganization]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeOrganization) return;
    setAddLoading(true);
    setAddError('');
    try {
      await organizationsService.addMember(activeOrganization.id, addEmail, addRoleId);
      setAddModalOpen(false);
      setAddEmail('');
      setAddRoleId('');
      fetchData(); // refresh list
    } catch (err) {
      setAddError(normalizeApiError(err));
    } finally {
      setAddLoading(false);
    }
  };

  const handleAssignRole = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeOrganization) return;
    setAssignLoading(true);
    setAssignError('');
    try {
      await rolesService.assignRole(activeOrganization.id, assignMemberId, assignRoleId);
      setAssignModalOpen(false);
      setAssignMemberId('');
      setAssignRoleId('');
      fetchData();
    } catch (err) {
      setAssignError(normalizeApiError(err));
    } finally {
      setAssignLoading(false);
    }
  };

  if (!activeOrganization) {
    return (
      <div className="flex flex-col items-center justify-center h-[50vh] text-center space-y-3">
        <AlertCircle className="h-12 w-12 text-gray-300" />
        <h2 className="text-xl font-semibold text-gray-900">No Active Organization</h2>
        <p className="text-gray-500">Select or create an organization to manage members.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-gray-900">Users &amp; Roles</h2>
          <p className="text-gray-500 mt-1">Members of <span className="font-medium">{activeOrganization.name}</span></p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => { setAssignModalOpen(true); setAssignError(''); }}
          >
            <Shield className="mr-2 h-4 w-4" />
            Assign Role
          </Button>
          <Button onClick={() => { setAddModalOpen(true); setAddError(''); }}>
            <UserPlus className="mr-2 h-4 w-4" />
            Add Member
          </Button>
        </div>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Members Table */}
      <div className="rounded-md border bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Roles</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Joined</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-10 text-gray-400">
                  Loading members...
                </TableCell>
              </TableRow>
            ) : members.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-10">
                  <div className="flex flex-col items-center gap-2 text-gray-400">
                    <Users className="h-8 w-8" />
                    <p className="font-medium text-gray-500">No members yet</p>
                    <p className="text-sm">Add a member to your organization to get started.</p>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              members.map((member) => (
                <TableRow key={member.id}>
                  <TableCell className="font-medium text-gray-900">
                    {member.first_name || ''} {member.last_name || ''}
                    {!member.first_name && !member.last_name && (
                      <span className="text-gray-400 italic">No name</span>
                    )}
                  </TableCell>
                  <TableCell className="text-gray-700">{member.email}</TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {member.roles.length === 0 ? (
                        <span className="text-xs text-gray-400 italic">No roles</span>
                      ) : (
                        member.roles.map((role) => (
                          <Badge key={role} variant="secondary" className="text-xs">
                            {role}
                          </Badge>
                        ))
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant={member.status === 'active' ? 'success' : 'secondary'}>
                      {member.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-gray-500 text-sm">
                    {member.joined_at ? new Date(member.joined_at).toLocaleDateString() : '—'}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Add Member Modal */}
      <Modal isOpen={addModalOpen} onClose={() => setAddModalOpen(false)} title="Add Member">
        <form onSubmit={handleAddMember} className="space-y-4 pt-2">
          <p className="text-sm text-gray-500">
            The person must already have a Cortex account. Enter their registered email address.
          </p>
          {addError && (
            <div className="rounded-md bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">
              {addError}
            </div>
          )}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700" htmlFor="add-member-email">Email Address</label>
            <Input
              id="add-member-email"
              type="email"
              placeholder="colleague@example.com"
              value={addEmail}
              onChange={(e) => setAddEmail(e.target.value)}
              required
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700" htmlFor="add-member-role">Assign Role</label>
            <select
              id="add-member-role"
              className="flex h-9 w-full rounded-md border border-gray-300 bg-white px-3 py-1 text-sm text-gray-900 shadow-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
              required
              value={addRoleId}
              onChange={(e) => setAddRoleId(e.target.value)}
            >
              <option value="" disabled>Select a role</option>
              {roles.map((r) => (
                <option key={r.id} value={r.id}>{r.name} {r.description ? `— ${r.description}` : ''}</option>
              ))}
            </select>
          </div>
          <div className="flex justify-end space-x-2 pt-4 border-t">
            <Button type="button" variant="outline" onClick={() => setAddModalOpen(false)}>Cancel</Button>
            <Button type="submit" disabled={addLoading || !addEmail || !addRoleId}>
              {addLoading ? 'Adding...' : 'Add Member'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Assign Role Modal */}
      <Modal isOpen={assignModalOpen} onClose={() => setAssignModalOpen(false)} title="Assign Role">
        <form onSubmit={handleAssignRole} className="space-y-4 pt-2">
          {assignError && (
            <div className="rounded-md bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">
              {assignError}
            </div>
          )}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">Member</label>
            <select
              className="flex h-9 w-full rounded-md border border-gray-300 bg-white px-3 py-1 text-sm text-gray-900 shadow-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
              required
              value={assignMemberId}
              onChange={(e) => setAssignMemberId(e.target.value)}
            >
              <option value="" disabled>Select a member</option>
              {members.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.first_name} {m.last_name} ({m.email})
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">Role</label>
            <select
              className="flex h-9 w-full rounded-md border border-gray-300 bg-white px-3 py-1 text-sm text-gray-900 shadow-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
              required
              value={assignRoleId}
              onChange={(e) => setAssignRoleId(e.target.value)}
            >
              <option value="" disabled>Select a role</option>
              {roles.map((r) => (
                <option key={r.id} value={r.id}>{r.name}</option>
              ))}
            </select>
          </div>
          <div className="flex justify-end space-x-2 pt-4 border-t">
            <Button type="button" variant="outline" onClick={() => setAssignModalOpen(false)}>Cancel</Button>
            <Button type="submit" disabled={assignLoading || !assignMemberId || !assignRoleId}>
              {assignLoading ? 'Assigning...' : 'Assign Role'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
