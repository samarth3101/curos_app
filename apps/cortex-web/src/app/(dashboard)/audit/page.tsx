"use client";

import { useEffect, useState } from 'react';
import { useOrgStore } from '@/stores/orgStore';
import { auditService } from '@/services/audit';
import type { components } from '@curos/types';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { format } from 'date-fns';

type AuditResponse = components['schemas']['AuditRecordResponse'];

export default function AuditPage() {
  const { activeOrganization } = useOrgStore();
  const [logs, setLogs] = useState<AuditResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    const fetchLogs = async () => {
      if (!activeOrganization) return;
      try {
        setLoading(true);
        const data = await auditService.list(activeOrganization.id, { size: 50 });
        setLogs(data.items);
        setTotal(data.total);
      } catch (error) {
        console.error('Failed to fetch audit logs:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchLogs();
  }, [activeOrganization]);

  if (!activeOrganization) {
    return (
      <div className="flex flex-col items-center justify-center h-[50vh] text-center">
        <h2 className="text-xl font-semibold mb-2 text-gray-900">No Active Organization</h2>
        <p className="text-gray-500">Please select an organization to view its audit logs.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-gray-900">Audit Log</h2>
          <p className="text-gray-500">Security and compliance events for {activeOrganization.name}. {total > 0 && `(${total} total)`}</p>
        </div>
      </div>

      <div className="rounded-md border bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Timestamp</TableHead>
              <TableHead>Action</TableHead>
              <TableHead>Resource</TableHead>
              <TableHead>Actor ID</TableHead>
              <TableHead>IP</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-8 text-gray-500">Loading audit logs...</TableCell>
              </TableRow>
            ) : logs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-8 text-gray-500">No audit logs yet. Actions taken in this organization will appear here.</TableCell>
              </TableRow>
            ) : (
              logs.map((log) => (
                <TableRow key={log.id}>
                  <TableCell className="whitespace-nowrap text-gray-700 text-sm">{format(new Date(log.timestamp), 'MMM d, HH:mm:ss')}</TableCell>
                  <TableCell className="font-medium text-blue-700 text-sm">{log.action}</TableCell>
                  <TableCell className="text-sm">
                    <span className="text-gray-700">{log.resource_type}</span>
                    <br />
                    <span className="text-xs text-gray-400 font-mono">{log.resource_id?.slice(0, 12)}...</span>
                  </TableCell>
                  <TableCell className="font-mono text-xs text-gray-600">{log.actor_id?.slice(0, 12)}...</TableCell>
                  <TableCell className="text-gray-400 text-xs">{log.ip_address || '–'}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
