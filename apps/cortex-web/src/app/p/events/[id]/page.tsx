"use client";

import { useEffect, useState, use } from 'react';
import { format } from 'date-fns';
import Image from 'next/image';
import { Calendar, MapPin, Users, Ticket, CheckCircle2, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { normalizeApiError } from '@/lib/errors';
import { isHttpError } from '@/lib/errors';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

interface PublicEvent {
  id: string;
  title: string;
  description: string | null;
  event_type: string;
  venue: string;
  start_at: string;
  end_at: string;
  capacity: number;
  registered_count: number;
  available_seats: number;
  status: string;
  organization_name: string;
}

interface TicketInfo {
  ticket_token: string;
  registration_id: string;
  participant_name: string;
  participant_email: string;
  event_title: string;
  event_type: string;
  event_date: string;
  event_venue: string;
  status: string;
  registered_at: string | null;
}

export default function PublicEventPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const eventId = resolvedParams.id;

  const [event, setEvent] = useState<PublicEvent | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  // Registration form
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [institution, setInstitution] = useState('');
  const [registering, setRegistering] = useState(false);
  const [regError, setRegError] = useState('');
  const [ticket, setTicket] = useState<TicketInfo | null>(null);

  // If user accesses with a ticket token in the URL
  const [ticketToken, setTicketToken] = useState('');
  const [lookingUpTicket, setLookingUpTicket] = useState(false);
  const [ticketLookupError, setTicketLookupError] = useState('');

  useEffect(() => {
    const fetchEvent = async () => {
      try {
        const res = await fetch(`${API_URL}/public/events/${eventId}`);
        if (res.status === 404) {
          setNotFound(true);
          return;
        }
        if (!res.ok) throw new Error('Failed to fetch event');
        const data = await res.json();
        setEvent(data);
      } catch (e) {
        console.error(e);
        setNotFound(true);
      } finally {
        setLoading(false);
      }
    };
    fetchEvent();
  }, [eventId]);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setRegError('');
    setRegistering(true);
    try {
      const res = await fetch(`${API_URL}/public/events/${eventId}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ full_name: fullName, email, phone: phone || undefined, institution: institution || undefined }),
      });

      const data = await res.json();

      if (res.status === 409) {
        setRegError('You are already registered for this event. Check your email for your ticket token.');
        return;
      }

      if (!res.ok) {
        setRegError(data?.detail || data?.error?.message || 'Registration failed. Please try again.');
        return;
      }

      setTicket({
        ticket_token: data.ticket_token,
        registration_id: data.registration_id,
        participant_name: data.participant_name,
        participant_email: data.participant_email,
        event_title: data.event_title,
        event_type: event?.event_type || '',
        event_date: data.event_date,
        event_venue: data.event_venue,
        status: 'REGISTERED',
        registered_at: new Date().toISOString(),
      });

      // Refresh available seats
      setEvent(prev => prev ? { ...prev, registered_count: prev.registered_count + 1, available_seats: prev.available_seats - 1 } : prev);
    } catch {
      setRegError('Network error. Please check your connection.');
    } finally {
      setRegistering(false);
    }
  };

  const handleTicketLookup = async (e: React.FormEvent) => {
    e.preventDefault();
    setTicketLookupError('');
    setLookingUpTicket(true);
    try {
      const res = await fetch(`${API_URL}/public/events/${eventId}/ticket/${ticketToken}`);
      if (res.status === 404) {
        setTicketLookupError('Ticket not found. Please check your token.');
        return;
      }
      const data = await res.json();
      if (!res.ok) {
        setTicketLookupError(data?.detail || 'Ticket lookup failed.');
        return;
      }
      setTicket(data);
    } catch {
      setTicketLookupError('Network error. Please try again.');
    } finally {
      setLookingUpTicket(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-2 border-blue-600 border-t-transparent rounded-full mx-auto mb-3" />
          <p className="text-gray-500">Loading event...</p>
        </div>
      </div>
    );
  }

  if (notFound || !event) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-sm p-8 bg-white rounded-xl shadow-sm">
          <AlertCircle className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <h1 className="text-xl font-bold text-gray-900">Event Not Found</h1>
          <p className="text-gray-500 mt-2 text-sm">
            This event doesn&apos;t exist, has been removed, or the link has expired.
          </p>
        </div>
      </div>
    );
  }

  const isOpen = event.status === 'PUBLISHED' || event.status === 'ONGOING';
  const isFull = event.available_seats <= 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-white">
      {/* Header bar */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3">
        <Image src="/curos_logo.png" alt="Curos" width={28} height={28} className="h-7 w-auto object-contain" />
        <span className="text-sm font-medium text-gray-600">
          <span className="text-red-600 font-bold">Cortex OI</span> — Event Portal
        </span>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8 lg:py-12">
        <div className="grid gap-8 lg:grid-cols-3">
          {/* Event Details */}
          <div className="lg:col-span-2 space-y-6">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="inline-block px-2.5 py-1 bg-blue-100 text-blue-700 text-xs font-semibold rounded-full">
                  {event.event_type}
                </span>
                <span className={`inline-block px-2.5 py-1 text-xs font-semibold rounded-full ${
                  event.status === 'PUBLISHED' ? 'bg-green-100 text-green-700' :
                  event.status === 'ONGOING' ? 'bg-purple-100 text-purple-700' :
                  'bg-gray-100 text-gray-600'
                }`}>
                  {event.status}
                </span>
              </div>
              <h1 className="text-3xl font-bold text-gray-900">{event.title}</h1>
              <p className="text-gray-500 mt-1 text-sm">by {event.organization_name}</p>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 shadow-xs p-6 space-y-4">
              <div className="flex items-center gap-3">
                <Calendar className="h-5 w-5 text-blue-500 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-gray-900">Date &amp; Time</p>
                  <p className="text-sm text-gray-600">
                    {format(new Date(event.start_at), 'EEEE, MMMM d, yyyy')} &bull; {format(new Date(event.start_at), 'h:mm a')} – {format(new Date(event.end_at), 'h:mm a')}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <MapPin className="h-5 w-5 text-blue-500 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-gray-900">Venue</p>
                  <p className="text-sm text-gray-600">{event.venue}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Users className="h-5 w-5 text-blue-500 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-gray-900">Capacity</p>
                  <p className="text-sm text-gray-600">
                    {event.registered_count} registered · {event.available_seats} seats remaining
                  </p>
                  <div className="mt-1.5 w-full bg-gray-200 rounded-full h-1.5">
                    <div
                      className="bg-blue-500 h-1.5 rounded-full"
                      style={{ width: `${Math.min(100, (event.registered_count / event.capacity) * 100)}%` }}
                    />
                  </div>
                </div>
              </div>
              {event.description && (
                <div className="pt-3 border-t border-gray-100">
                  <p className="text-sm font-medium text-gray-900 mb-1">About this event</p>
                  <p className="text-sm text-gray-600 whitespace-pre-wrap">{event.description}</p>
                </div>
              )}
            </div>

            {/* Ticket Lookup */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Ticket className="h-4 w-4 text-blue-500" />
                  Already registered? View your ticket
                </CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleTicketLookup} className="flex gap-2">
                  <Input
                    placeholder="Enter your ticket token"
                    value={ticketToken}
                    onChange={(e) => setTicketToken(e.target.value)}
                    className="flex-1 font-mono text-sm"
                    required
                  />
                  <Button type="submit" variant="outline" disabled={lookingUpTicket}>
                    {lookingUpTicket ? '...' : 'View Ticket'}
                  </Button>
                </form>
                {ticketLookupError && (
                  <p className="text-sm text-red-600 mt-2">{ticketLookupError}</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Right Column — Registration Form or Ticket */}
          <div className="space-y-4">
            {ticket ? (
              /* Ticket Display */
              <div className="bg-white rounded-xl border-2 border-blue-200 shadow-md overflow-hidden">
                <div className="bg-blue-600 px-6 py-4 text-white">
                  <div className="flex items-center gap-2 mb-1">
                    <CheckCircle2 className="h-5 w-5" />
                    <span className="font-semibold">Registration Confirmed</span>
                  </div>
                  <p className="text-blue-100 text-sm">{ticket.event_title}</p>
                </div>
                <div className="px-6 py-4 space-y-3">
                  <div>
                    <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">Attendee</p>
                    <p className="text-gray-900 font-semibold">{ticket.participant_name}</p>
                    <p className="text-gray-500 text-sm">{ticket.participant_email}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">Date</p>
                    <p className="text-gray-900 text-sm">{format(new Date(ticket.event_date), 'EEEE, MMM d, yyyy')}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">Venue</p>
                    <p className="text-gray-900 text-sm">{ticket.event_venue}</p>
                  </div>
                  <div className="pt-3 border-t border-dashed border-gray-200">
                    <p className="text-xs text-gray-500 font-medium uppercase tracking-wider mb-1">Ticket Token</p>
                    <code className="block bg-gray-50 rounded p-2 text-xs text-gray-700 font-mono break-all">
                      {ticket.ticket_token}
                    </code>
                    <p className="text-xs text-gray-400 mt-1">Keep this token safe — it&apos;s your proof of registration.</p>
                  </div>
                </div>
              </div>
            ) : isOpen && !isFull ? (
              /* Registration Form */
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
                <div className="px-6 pt-6 pb-2">
                  <h2 className="text-lg font-bold text-gray-900">Register for this Event</h2>
                  <p className="text-sm text-gray-500 mt-0.5">Free &bull; {event.available_seats} spots left</p>
                </div>
                <form onSubmit={handleRegister} className="px-6 pb-6 space-y-4 pt-3">
                  {regError && (
                    <div className={`rounded-md px-3 py-2 text-sm ${regError.includes('already registered') ? 'bg-amber-50 text-amber-700 border border-amber-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
                      {regError}
                    </div>
                  )}
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-gray-700" htmlFor="reg-name">Full Name *</label>
                    <Input id="reg-name" placeholder="Your full name" value={fullName} onChange={(e) => setFullName(e.target.value)} required />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-gray-700" htmlFor="reg-email">Email Address *</label>
                    <Input id="reg-email" type="email" placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} required />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-gray-700" htmlFor="reg-phone">Phone <span className="text-gray-400 font-normal">(optional)</span></label>
                    <Input id="reg-phone" type="tel" placeholder="+91 00000 00000" value={phone} onChange={(e) => setPhone(e.target.value)} />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-gray-700" htmlFor="reg-institution">Institution <span className="text-gray-400 font-normal">(optional)</span></label>
                    <Input id="reg-institution" placeholder="Your college or company" value={institution} onChange={(e) => setInstitution(e.target.value)} />
                  </div>
                  <Button type="submit" className="w-full" disabled={registering}>
                    {registering ? 'Registering...' : 'Register Now →'}
                  </Button>
                  <p className="text-xs text-gray-400 text-center">
                    You&apos;ll receive a ticket token after registration. Save it to access your ticket later.
                  </p>
                </form>
              </div>
            ) : (
              /* Closed / Full */
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 text-center">
                <AlertCircle className="h-10 w-10 text-gray-300 mx-auto mb-3" />
                <p className="font-semibold text-gray-700">
                  {isFull ? 'Event is Full' : 'Registration Closed'}
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  {isFull
                    ? 'This event has reached its capacity.'
                    : `This event is currently ${event.status.toLowerCase()} and not accepting registrations.`}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
