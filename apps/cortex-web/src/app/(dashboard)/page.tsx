"use client";

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useOrgStore } from '@/stores/orgStore';
import { organizationsService, type OrgStats } from '@/services/organizations';
import { eventsService } from '@/services/events';
import { auditService } from '@/services/audit';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Users,
  Calendar,
  TrendingUp,
  Clock,
  CheckSquare,
  Ticket,
  UserCheck,
  AlertCircle,
  ArrowRight,
  Building2,
} from 'lucide-react';
import type { components } from '@curos/types';

type EventResponse = components['schemas']['EventResponse'];
type AuditRecord = components['schemas']['AuditRecordResponse'];

const ACTION_LABELS: Record<string, string> = {
  'event.created': 'Event Created',
  'event.submitted': 'Event Submitted',
  'event.approved': 'Event Approved',
  'event.rejected': 'Event Rejected',
  'event.published': 'Event Published',
  'event.started': 'Event Started',
  'event.completed': 'Event Completed',
  'event.archived': 'Event Archived',
  'event.registration_created': 'Registration',
  'event.guest_registration_created': 'Guest Registration',
  'event.attendance_recorded': 'Attendance Recorded',
  'member.added': 'Member Added',
  'member.role_assigned': 'Role Assigned',
  'organization.created': 'Organization Created',
  'role.created': 'Role Created',
};

function StatCard({
  icon: Icon,
  label,
  value,
  color = 'blue',
}: {
  icon: React.ElementType;
  label: string;
  value: number | string;
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'purple';
}) {
  const colorMap = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    red: 'bg-red-50 text-red-600',
    purple: 'bg-purple-50 text-purple-600',
  };

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center gap-4">
          <div className={`h-10 w-10 rounded-lg flex items-center justify-center ${colorMap[color]}`}>
            <Icon className="h-5 w-5" />
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900">{value}</p>
            <p className="text-sm text-gray-500">{label}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function EventStatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    DRAFT: 'bg-gray-100 text-gray-700',
    SUBMITTED: 'bg-yellow-100 text-yellow-700',
    APPROVED: 'bg-blue-100 text-blue-700',
    PUBLISHED: 'bg-green-100 text-green-700',
    ONGOING: 'bg-purple-100 text-purple-700',
    COMPLETED: 'bg-gray-200 text-gray-600',
    ARCHIVED: 'bg-gray-100 text-gray-500',
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${map[status] || 'bg-gray-100 text-gray-700'}`}>
      {status}
    </span>
  );
}

export default function DashboardPage() {
  const { activeOrganization } = useOrgStore();
  const [stats, setStats] = useState<OrgStats | null>(null);
  const [recentEvents, setRecentEvents] = useState<EventResponse[]>([]);
  const [recentActivity, setRecentActivity] = useState<AuditRecord[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchDashboard = useCallback(async () => {
    if (!activeOrganization) return;
    setLoading(true);
    try {
      const [statsData, eventsData, auditData] = await Promise.all([
        organizationsService.getStats(activeOrganization.id),
        eventsService.list(activeOrganization.id),
        auditService.list(activeOrganization.id, { page: 1, size: 6 }),
      ]);
      setStats(statsData);
      // Show latest 4 events
      setRecentEvents([...eventsData].sort((a, b) =>
        new Date(b.created_at ?? 0).getTime() - new Date(a.created_at ?? 0).getTime()
      ).slice(0, 4));
      setRecentActivity(auditData.items || []);
    } catch (e) {
      console.error('Dashboard fetch failed', e);
    } finally {
      setLoading(false);
    }
  }, [activeOrganization]);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  if (!activeOrganization) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-center space-y-4">
        <Building2 className="h-16 w-16 text-gray-200" />
        <div>
          <h2 className="text-xl font-semibold text-gray-900">No Organization Selected</h2>
          <p className="text-gray-500 mt-1">Create or select an organization to view your dashboard.</p>
        </div>
        <Link href="/onboarding" className="text-blue-600 hover:underline text-sm font-medium flex items-center gap-1">
          Get started <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Org Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">{activeOrganization.name}</h2>
        <p className="text-gray-500 text-sm capitalize">{activeOrganization.type} · {activeOrganization.slug}</p>
      </div>

      {/* Stats Grid */}
      {loading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="pt-6">
                <div className="h-10 bg-gray-100 rounded animate-pulse" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : stats ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <StatCard icon={Users} label="Total Members" value={stats.total_members} color="blue" />
          <StatCard icon={Calendar} label="Total Events" value={stats.total_events} color="purple" />
          <StatCard icon={TrendingUp} label="Upcoming Events" value={stats.upcoming_events} color="green" />
          <StatCard icon={Clock} label="Pending Approvals" value={stats.pending_approvals} color="yellow" />
          <StatCard icon={Ticket} label="Registrations" value={stats.total_registrations} color="blue" />
          <StatCard icon={UserCheck} label="Attendance" value={stats.total_attendance} color="green" />
        </div>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Recent Events */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle className="text-base">Recent Events</CardTitle>
              <CardDescription>Latest events in your organization</CardDescription>
            </div>
            <Link href="/events" className="text-sm text-blue-600 hover:underline flex items-center gap-1">
              View all <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </CardHeader>
          <CardContent>
            {recentEvents.length === 0 ? (
              <div className="flex flex-col items-center py-6 text-gray-400 gap-2">
                <Calendar className="h-8 w-8" />
                <p className="text-sm">No events yet.</p>
                <Link href="/events" className="text-sm text-blue-600 hover:underline">Create your first event</Link>
              </div>
            ) : (
              <div className="space-y-3">
                {recentEvents.map((event) => (
                  <Link
                    key={event.id}
                    href={`/events/${event.id}`}
                    className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <div>
                      <p className="text-sm font-medium text-gray-900">{event.title}</p>
                      <p className="text-xs text-gray-500">{event.venue}</p>
                    </div>
                    <EventStatusBadge status={event.status} />
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle className="text-base">Recent Activity</CardTitle>
              <CardDescription>Latest actions in your organization</CardDescription>
            </div>
            <Link href="/audit" className="text-sm text-blue-600 hover:underline flex items-center gap-1">
              View all <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </CardHeader>
          <CardContent>
            {recentActivity.length === 0 ? (
              <div className="flex flex-col items-center py-6 text-gray-400 gap-2">
                <AlertCircle className="h-8 w-8" />
                <p className="text-sm">No activity recorded yet.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {recentActivity.map((log) => (
                  <div key={log.id} className="flex items-start gap-3">
                    <div className="h-2 w-2 rounded-full bg-blue-400 mt-1.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900">
                        {ACTION_LABELS[log.action] || log.action}
                      </p>
                      <p className="text-xs text-gray-500">
                        {new Date(log.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
