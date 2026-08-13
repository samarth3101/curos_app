"use client";

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useOrgStore } from '@/stores/orgStore';
import { eventsService } from '@/services/events';
import type { components } from '@curos/types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Modal } from '@/components/ui/modal';
import { Badge } from '@/components/ui/badge';
import { Plus } from 'lucide-react';
import { format } from 'date-fns';

type EventResponse = components['schemas']['EventResponse'];
type EventType = components['schemas']['EventType'];

export default function EventsPage() {
  const { activeOrganization } = useOrgStore();
  const [events, setEvents] = useState<EventResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    event_type: 'WORKSHOP' as EventType,
    venue: '',
    start_at: '',
    end_at: '',
    capacity: 100,
  });

  const fetchEvents = useCallback(async () => {
    if (!activeOrganization) return;
    try {
      setLoading(true);
      const data = await eventsService.list(activeOrganization.id);
      setEvents(data);
    } catch (error) {
      console.error('Failed to fetch events:', error);
    } finally {
      setLoading(false);
    }
  }, [activeOrganization]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchEvents();
  }, [fetchEvents]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeOrganization) return;
    setIsSubmitting(true);
    try {
      const startAtISO = new Date(formData.start_at).toISOString();
      const endAtISO = new Date(formData.end_at).toISOString();

      const newEvent = await eventsService.create(activeOrganization.id, {
        ...formData,
        start_at: startAtISO,
        end_at: endAtISO,
      });

      setEvents([...events, newEvent]);
      setIsCreateModalOpen(false);
      setFormData({ title: '', description: '', event_type: 'WORKSHOP', venue: '', start_at: '', end_at: '', capacity: 100 });
    } catch (error) {
      const axiosError = error as { response?: { data?: { detail?: string } } };
      console.error('Failed to create event:', error);
      alert(axiosError.response?.data?.detail || 'Failed to create event');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'DRAFT': return <Badge variant="secondary">{status}</Badge>;
      case 'SUBMITTED': return <Badge variant="warning">{status}</Badge>;
      case 'APPROVED': return <Badge variant="default">{status}</Badge>;
      case 'PUBLISHED': return <Badge variant="success">{status}</Badge>;
      case 'ONGOING': return <Badge variant="default">{status}</Badge>;
      case 'COMPLETED': return <Badge variant="outline">{status}</Badge>;
      default: return <Badge variant="outline">{status}</Badge>;
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
          <h2 className="text-2xl font-bold tracking-tight text-gray-900">Events</h2>
          <p className="text-gray-500">Manage events for {activeOrganization.name}.</p>
        </div>
        <Button onClick={() => setIsCreateModalOpen(true)}>
          <Plus className="mr-2 h-4 w-4" /> Create Event
        </Button>
      </div>

      <div className="rounded-md border bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Title</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Date</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-8 text-gray-500">Loading events...</TableCell>
              </TableRow>
            ) : events.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-8 text-gray-500">No events yet. Click &quot;Create Event&quot; to start.</TableCell>
              </TableRow>
            ) : (
              events.map((event) => (
                <TableRow key={event.id}>
                  <TableCell className="font-medium text-gray-900">{event.title}</TableCell>
                  <TableCell className="text-gray-700">{event.event_type}</TableCell>
                  <TableCell className="text-gray-700">{format(new Date(event.start_at), 'PPP')}</TableCell>
                  <TableCell>{getStatusBadge(event.status)}</TableCell>
                  <TableCell className="text-right">
                    <Button variant="outline" size="sm" asChild>
                      <Link href={`/events/${event.id}?orgId=${activeOrganization.id}`}>View Details</Link>
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      <Modal isOpen={isCreateModalOpen} onClose={() => setIsCreateModalOpen(false)} title="Create Event">
        <form onSubmit={handleCreate} className="space-y-4 pt-4 max-h-[70vh] overflow-y-auto px-1">
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">Title</label>
            <Input required value={formData.title} onChange={e => setFormData({ ...formData, title: e.target.value })} placeholder="e.g. Annual Tech Symposium" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">Description</label>
            <textarea
              className="flex w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm placeholder:text-gray-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
              rows={3}
              value={formData.description}
              onChange={e => setFormData({ ...formData, description: e.target.value })}
              placeholder="Optional description..."
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">Event Type</label>
              <select
                className="flex h-9 w-full rounded-md border border-gray-300 bg-white px-3 py-1 text-sm text-gray-900 shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                value={formData.event_type}
                onChange={e => setFormData({ ...formData, event_type: e.target.value as EventType })}
              >
                <option value="WORKSHOP">Workshop</option>
                <option value="SEMINAR">Seminar</option>
                <option value="HACKATHON">Hackathon</option>
                <option value="CONFERENCE">Conference</option>
                <option value="OTHER">Other</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">Capacity</label>
              <Input type="number" required value={formData.capacity} onChange={e => setFormData({ ...formData, capacity: parseInt(e.target.value) })} min={1} />
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">Venue</label>
            <Input required value={formData.venue} onChange={e => setFormData({ ...formData, venue: e.target.value })} placeholder="e.g. Main Auditorium" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">Start Date & Time</label>
              <Input type="datetime-local" required value={formData.start_at} onChange={e => setFormData({ ...formData, start_at: e.target.value })} />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">End Date & Time</label>
              <Input type="datetime-local" required value={formData.end_at} onChange={e => setFormData({ ...formData, end_at: e.target.value })} />
            </div>
          </div>

          <div className="flex justify-end space-x-2 pt-4 border-t">
            <Button type="button" variant="outline" onClick={() => setIsCreateModalOpen(false)}>Cancel</Button>
            <Button type="submit" disabled={isSubmitting}>{isSubmitting ? 'Creating...' : 'Create Event'}</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
