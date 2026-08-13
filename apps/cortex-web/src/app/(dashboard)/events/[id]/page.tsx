"use client";

import { useCallback, useEffect, useState, use } from 'react';
import { useSearchParams } from 'next/navigation';
import { useOrgStore } from '@/stores/orgStore';
import { useAuthStore } from '@/stores/authStore';
import { eventsService } from '@/services/events';
import type { components } from '@curos/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { format } from 'date-fns';
import { Calendar, MapPin, Users, Activity, CheckCircle2 } from 'lucide-react';

type EventResponse = components['schemas']['EventResponse'];
type EventRegistrationResponse = components['schemas']['EventRegistrationResponse'];
type EventAttendanceResponse = components['schemas']['EventAttendanceResponse'];

export default function EventDetailsPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const eventId = resolvedParams.id;
  const searchParams = useSearchParams();
  const { activeOrganization } = useOrgStore();
  const { user } = useAuthStore();

  // Prefer orgId from query param (passed from list page), fall back to store
  const orgId = searchParams.get('orgId') || activeOrganization?.id || '';

  const [event, setEvent] = useState<EventResponse | null>(null);
  const [registrations, setRegistrations] = useState<EventRegistrationResponse[]>([]);
  const [attendance, setAttendance] = useState<EventAttendanceResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState('');

  const fetchEventData = useCallback(async () => {
    if (!orgId) return;
    try {
      setLoading(true);
      const [eventData, regsData, attData] = await Promise.all([
        eventsService.getById(orgId, eventId),
        eventsService.getRegistrations(orgId, eventId),
        eventsService.getAttendance(orgId, eventId),
      ]);
      setEvent(eventData);
      setRegistrations(regsData);
      setAttendance(attData);
    } catch (error) {
      console.error('Failed to fetch event data:', error);
    } finally {
      setLoading(false);
    }
  }, [orgId, eventId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchEventData();
  }, [fetchEventData]);


  const handleAction = async (actionFn: () => Promise<unknown>, label: string) => {
    setActionLoading(true);
    setActionError('');
    try {
      await actionFn();
      await fetchEventData();
    } catch (error) {
      const axiosErr = error as { response?: { data?: { detail?: string; error?: { message?: string } } } };
      const msg = axiosErr.response?.data?.detail || axiosErr.response?.data?.error?.message || `${label} failed`;
      setActionError(msg);
      console.error(`${label} failed:`, axiosErr.response?.data || error);
    } finally {
      setActionLoading(false);
    }
  };

  const isRegistered = registrations.some(r => r.user_id === user?.id && r.status === 'REGISTERED');
  const hasAttended = attendance.some(a => a.user_id === user?.id);

  if (!orgId) {
    return (
      <div className="p-8 text-center text-gray-700">
        <p className="text-lg font-semibold">No Organization Context</p>
        <p className="text-gray-500 mt-1">Please select an organization and navigate to this event from the Events tab.</p>
      </div>
    );
  }

  if (loading && !event) {
    return <div className="p-8 text-center text-gray-500">Loading event details...</div>;
  }

  if (!event) {
    return <div className="p-8 text-center text-red-600">Event not found.</div>;
  }

  const workflowSteps = [
    { status: 'DRAFT', label: 'Draft' },
    { status: 'SUBMITTED', label: 'Submitted' },
    { status: 'APPROVED', label: 'Approved' },
    { status: 'PUBLISHED', label: 'Published' },
    { status: 'ONGOING', label: 'Ongoing' },
    { status: 'COMPLETED', label: 'Completed' },
  ];

  const currentStepIndex = workflowSteps.findIndex(s => s.status === event.status);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-gray-900">{event.title}</h2>
          <div className="text-gray-500 flex items-center mt-1 gap-2">
            <Badge variant="outline">{event.event_type}</Badge>
            <span className="font-medium text-gray-700">Status: {event.status}</span>
          </div>
        </div>

        {/* Lifecycle Action Buttons */}
        <div className="flex flex-wrap gap-2">
          {actionError && (
            <div className="w-full text-sm text-red-600 bg-red-50 border border-red-200 px-3 py-2 rounded-md">
              {actionError}
            </div>
          )}
          {event.status === 'DRAFT' && (
            <Button onClick={() => handleAction(() => eventsService.submit(orgId, event.id), 'Submit')} disabled={actionLoading}>
              {actionLoading ? '...' : 'Submit for Approval'}
            </Button>
          )}
          {event.status === 'SUBMITTED' && (
            <>
              <Button variant="destructive" onClick={() => handleAction(() => eventsService.reject(orgId, event.id), 'Reject')} disabled={actionLoading}>
                Reject
              </Button>
              <Button className="bg-green-600 text-white hover:bg-green-700" onClick={() => handleAction(() => eventsService.approve(orgId, event.id), 'Approve')} disabled={actionLoading}>
                Approve
              </Button>
            </>
          )}
          {event.status === 'APPROVED' && (
            <Button onClick={() => handleAction(() => eventsService.publish(orgId, event.id), 'Publish')} disabled={actionLoading}>
              {actionLoading ? '...' : 'Publish Event'}
            </Button>
          )}
          {event.status === 'PUBLISHED' && (
            <Button className="bg-orange-600 text-white hover:bg-orange-700" onClick={() => handleAction(() => eventsService.start(orgId, event.id), 'Start')} disabled={actionLoading}>
              {actionLoading ? '...' : 'Start Event (→ Ongoing)'}
            </Button>
          )}
          {event.status === 'ONGOING' && (
            <Button onClick={() => handleAction(() => eventsService.complete(orgId, event.id), 'Complete')} disabled={actionLoading}>
              {actionLoading ? '...' : 'Complete Event'}
            </Button>
          )}
          {event.status === 'COMPLETED' && (
            <Button variant="outline" onClick={() => handleAction(() => eventsService.archive(orgId, event.id), 'Archive')} disabled={actionLoading}>
              Archive
            </Button>
          )}
        </div>
      </div>

      {/* Workflow Timeline */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center overflow-x-auto pb-4 gap-0">
            {workflowSteps.map((step, index) => {
              const isPast = index < currentStepIndex;
              const isCurrent = index === currentStepIndex;

              return (
                <div key={step.status} className="flex items-center">
                  <div className="flex flex-col items-center mx-3">
                    <div className={`flex items-center justify-center w-8 h-8 rounded-full border-2 ${
                      isPast ? 'bg-blue-600 border-blue-600' :
                      isCurrent ? 'border-blue-600 bg-white' :
                      'border-gray-300 bg-white'
                    }`}>
                      {isPast ? (
                        <CheckCircle2 className="w-5 h-5 text-white" />
                      ) : isCurrent ? (
                        <div className="w-3 h-3 bg-blue-600 rounded-full" />
                      ) : null}
                    </div>
                    <span className={`text-xs mt-2 font-medium whitespace-nowrap ${isCurrent ? 'text-blue-600' : isPast ? 'text-gray-700' : 'text-gray-400'}`}>
                      {step.label}
                    </span>
                  </div>
                  {index < workflowSteps.length - 1 && (
                    <div className={`h-0.5 w-12 md:w-16 ${isPast ? 'bg-blue-600' : 'bg-gray-200'}`} />
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 md:grid-cols-3">
        {/* Info Column */}
        <div className="md:col-span-1 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-gray-900">Event Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-start">
                <Calendar className="mr-3 h-5 w-5 text-gray-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-gray-700">Date & Time</p>
                  <p className="text-sm text-gray-600">{format(new Date(event.start_at), 'PPP p')} – {format(new Date(event.end_at), 'p')}</p>
                </div>
              </div>
              <div className="flex items-start">
                <MapPin className="mr-3 h-5 w-5 text-gray-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-gray-700">Venue</p>
                  <p className="text-sm text-gray-600">{event.venue}</p>
                </div>
              </div>
              <div className="flex items-start">
                <Users className="mr-3 h-5 w-5 text-gray-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-gray-700">Capacity</p>
                  <p className="text-sm text-gray-600">{registrations.length} / {event.capacity} registered</p>
                </div>
              </div>
              {event.description && (
                <div className="pt-3 border-t border-gray-100">
                  <p className="text-sm font-medium text-gray-700 mb-1">Description</p>
                  <p className="text-sm text-gray-600 whitespace-pre-wrap">{event.description}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Participant Flow Card */}
          <Card className="border-blue-200 bg-blue-50">
            <CardHeader>
              <CardTitle className="text-blue-900 flex items-center text-base">
                <Activity className="mr-2 w-4 h-4" />
                Test Participant Flow
              </CardTitle>
              <CardDescription className="text-blue-700">Simulate actions as your current user</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {!isRegistered ? (
                <Button
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white"
                  disabled={actionLoading || (event.status !== 'PUBLISHED' && event.status !== 'ONGOING')}
                  onClick={() => handleAction(() => eventsService.register(orgId, event.id), 'Register')}
                >
                  {actionLoading ? 'Processing...' : 'Register Now'}
                </Button>
              ) : (
                <div className="space-y-3">
                  <Badge variant="success" className="w-full justify-center py-1.5 text-sm">✓ You are registered</Badge>
                  {!hasAttended ? (
                    <Button
                      className="w-full"
                      variant="outline"
                      disabled={actionLoading || event.status !== 'ONGOING'}
                      onClick={() => handleAction(() => eventsService.recordAttendance(orgId, event.id, { user_id: user!.id, method: 'MANUAL' }), 'Record Attendance')}
                    >
                      {actionLoading ? 'Processing...' : 'Mark Manual Attendance'}
                    </Button>
                  ) : (
                    <Badge variant="default" className="w-full justify-center py-1.5 bg-green-100 text-green-800 border-green-200 text-sm">✓ Attendance Recorded</Badge>
                  )}
                </div>
              )}
              {(event.status !== 'PUBLISHED' && event.status !== 'ONGOING') && !isRegistered && (
                <p className="text-xs text-blue-600">Registration opens when event is Published or Ongoing.</p>
              )}
              {isRegistered && event.status !== 'ONGOING' && !hasAttended && (
                <p className="text-xs text-blue-600">Attendance can only be marked when event is Ongoing.</p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Data Tables */}
        <div className="md:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-gray-900">Registrations ({registrations.length})</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>User ID</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Registered At</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {registrations.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={3} className="text-center py-4 text-gray-500">No registrations yet.</TableCell>
                    </TableRow>
                  ) : (
                    registrations.map(reg => (
                      <TableRow key={reg.id}>
                        <TableCell className="font-mono text-xs text-gray-700">{reg.user_id}</TableCell>
                        <TableCell>
                          <Badge variant={reg.status === 'REGISTERED' ? 'success' : 'secondary'}>{reg.status}</Badge>
                        </TableCell>
                        <TableCell className="text-gray-700">{reg.registered_at ? format(new Date(reg.registered_at), 'MMM d, p') : '–'}</TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-gray-900">Attendance ({attendance.length})</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>User ID</TableHead>
                    <TableHead>Method</TableHead>
                    <TableHead>Checked In</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {attendance.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={3} className="text-center py-4 text-gray-500">No attendance recorded yet.</TableCell>
                    </TableRow>
                  ) : (
                    attendance.map(att => (
                      <TableRow key={att.id}>
                        <TableCell className="font-mono text-xs text-gray-700">{att.user_id}</TableCell>
                        <TableCell><Badge variant="outline">{att.method}</Badge></TableCell>
                        <TableCell className="text-gray-700">{format(new Date(att.checked_in_at), 'MMM d, p')}</TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
