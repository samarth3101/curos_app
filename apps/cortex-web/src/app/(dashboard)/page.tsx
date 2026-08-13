"use client";

import { useEffect, useState } from 'react';
import { useOrgStore } from '@/stores/orgStore';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle2, Circle } from 'lucide-react';
import { eventsService } from '@/services/events';
import { usersService } from '@/services/users';
import { rolesService } from '@/services/roles';

export default function DashboardPage() {
  const { activeOrganization } = useOrgStore();
  const [stats, setStats] = useState({
    eventsCount: 0,
    usersCount: 0,
    rolesCount: 0,
  });

  useEffect(() => {
    const fetchStats = async () => {
      if (!activeOrganization) return;
      try {
        const [events, roles, users] = await Promise.all([
          eventsService.list(activeOrganization.id),
          rolesService.list(activeOrganization.id),
          usersService.listOrganizationMembers(activeOrganization.id),
        ]);
        
        setStats({
          eventsCount: events.length,
          usersCount: users.length,
          rolesCount: roles.length,
        });
      } catch (e) {
        console.error("Failed to fetch dashboard stats", e);
      }
    };
    
    fetchStats();
  }, [activeOrganization]);

  const verificationSteps = [
    { name: 'Organization', done: !!activeOrganization },
    { name: 'Users', done: stats.usersCount > 0 },
    { name: 'Roles', done: stats.rolesCount > 0 },
    { name: 'Event', done: stats.eventsCount > 0 },
    // Simplified for the dashboard view
    { name: 'Approval', done: false },
    { name: 'Publish', done: false },
    { name: 'Registration', done: false },
    { name: 'Attendance', done: false },
    { name: 'Complete', done: false },
    { name: 'Audit', done: false },
  ];

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Organization</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeOrganization ? activeOrganization.name : 'None'}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Users</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.usersCount}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Roles</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.rolesCount}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Events</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.eventsCount}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Product Verification Flow</CardTitle>
          <CardDescription>
            Complete these steps to verify the entire Cortex OI platform lifecycle.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2 items-center">
            {verificationSteps.map((step, index) => (
              <div key={step.name} className="flex items-center">
                <div className={`flex items-center space-x-2 px-3 py-2 rounded-md border ${step.done ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'}`}>
                  {step.done ? (
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                  ) : (
                    <Circle className="h-4 w-4 text-gray-400" />
                  )}
                  <span className={`text-sm font-medium ${step.done ? 'text-green-800' : 'text-gray-600'}`}>
                    {step.name}
                  </span>
                </div>
                {index < verificationSteps.length - 1 && (
                  <div className="mx-2 text-gray-400">→</div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
