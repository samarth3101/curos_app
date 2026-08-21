"use client";

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { useAuthStore } from '@/stores/authStore';
import { useOrgStore } from '@/stores/orgStore';
import { LayoutDashboard, Building2, Users, Calendar, ShieldAlert, LogOut, ChevronDown, Plus } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, clearAuth } = useAuthStore();
  const { activeOrganization, organizations, setActiveOrganization } = useOrgStore();
  const router = useRouter();
  const pathname = usePathname();

  // --- Session Persistence Fix (E1) ---
  // Do NOT redirect until Zustand has fully hydrated from localStorage.
  // Without this, refreshing the page wipes the session because the
  // redirect fires before the persist middleware restores the token.
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    // useAuthStore.persist.hasHydrated() is true only after localStorage is loaded
    if (useAuthStore.persist.hasHydrated()) {
      setHydrated(true);
    } else {
      const unsub = useAuthStore.persist.onFinishHydration(() => {
        setHydrated(true);
      });
      return unsub;
    }
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    if (!user) {
      router.push('/login');
    }
  }, [hydrated, user, router]);

  const [orgDropdownOpen, setOrgDropdownOpen] = useState(false);

  if (!hydrated) {
    // Show a minimal loading state during hydration to prevent flash
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <div className="text-center space-y-3">
          <Image src="/curos_logo.png" alt="Curos Logo" width={48} height={48} className="h-12 w-auto object-contain mx-auto" />
          <div className="h-1 w-32 bg-gray-200 rounded-full overflow-hidden mx-auto">
            <div className="h-full w-full bg-red-600 rounded-full animate-pulse" />
          </div>
        </div>
      </div>
    );
  }

  if (!user) return null;

  const handleLogout = () => {
    clearAuth();
    useOrgStore.getState().clearActiveOrganization();
    router.push('/login');
  };

  const navItems = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Organizations', href: '/organizations', icon: Building2 },
    { name: 'Users & Roles', href: '/users', icon: Users },
    { name: 'Events', href: '/events', icon: Calendar },
    { name: 'Audit Log', href: '/audit', icon: ShieldAlert },
  ];

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="h-16 flex items-center px-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <Image src="/curos_logo.png" alt="Curos Logo" width={32} height={32} className="h-8 w-8 object-contain" />
            <span className="text-lg font-bold text-gray-900 tracking-tight">Cortex <span className="text-red-600">OI</span></span>
          </div>
        </div>
        
        <div className="flex-1 overflow-y-auto py-4">
          <nav className="space-y-1 px-3">
            {navItems.map((item) => {
              const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    "flex items-center px-3 py-2 text-sm font-medium rounded-md",
                    isActive 
                      ? "bg-blue-50 text-blue-700" 
                      : "text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                  )}
                >
                  <item.icon className={cn(
                    "mr-3 h-5 w-5 flex-shrink-0",
                    isActive ? "text-blue-700" : "text-gray-400"
                  )} />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="p-4 border-t border-gray-200">
          <div className="flex items-center">
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-700">{user.first_name} {user.last_name}</p>
              <button onClick={handleLogout} className="text-xs font-medium text-red-600 hover:text-red-500 flex items-center mt-1">
                <LogOut className="h-3 w-3 mr-1" />
                Sign out
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-8">
          <h1 className="text-xl font-semibold text-gray-900">
            {navItems.find(i => i.href === pathname || (i.href !== '/' && pathname.startsWith(i.href)))?.name || 'Dashboard'}
          </h1>
          
          <div className="flex items-center space-x-4">
            {/* Organization Switcher */}
            <div className="relative">
              <button
                onClick={() => setOrgDropdownOpen(!orgDropdownOpen)}
                className={cn(
                  "inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium border transition-colors",
                  activeOrganization
                    ? "bg-green-50 text-green-800 border-green-200 hover:bg-green-100"
                    : "bg-yellow-50 text-yellow-800 border-yellow-200 hover:bg-yellow-100"
                )}
              >
                <span className={cn("h-2 w-2 rounded-full", activeOrganization ? "bg-green-500" : "bg-yellow-500")} />
                {activeOrganization ? activeOrganization.name : 'No Organization'}
                {organizations.length > 1 && <ChevronDown className="h-3 w-3" />}
              </button>

              {orgDropdownOpen && organizations.length > 0 && (
                <div className="absolute right-0 top-full mt-1 w-56 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
                  <div className="py-1">
                    <p className="px-3 py-1.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">Switch Organization</p>
                    {organizations.map((org) => (
                      <button
                        key={org.id}
                        onClick={() => {
                          setActiveOrganization(org);
                          setOrgDropdownOpen(false);
                        }}
                        className={cn(
                          "w-full text-left px-3 py-2 text-sm hover:bg-gray-50 flex items-center gap-2",
                          activeOrganization?.id === org.id ? "text-blue-700 font-medium" : "text-gray-700"
                        )}
                      >
                        <span className={cn("h-1.5 w-1.5 rounded-full", activeOrganization?.id === org.id ? "bg-blue-500" : "bg-gray-300")} />
                        {org.name}
                      </button>
                    ))}
                    <div className="border-t border-gray-100 mt-1">
                      <Link
                        href="/onboarding"
                        onClick={() => setOrgDropdownOpen(false)}
                        className="w-full text-left px-3 py-2 text-sm text-gray-500 hover:bg-gray-50 flex items-center gap-2"
                      >
                        <Plus className="h-3.5 w-3.5" />
                        New Organization
                      </Link>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-8">
          {children}
        </main>
      </div>

      {/* Click-outside to close org dropdown */}
      {orgDropdownOpen && (
        <div className="fixed inset-0 z-40" onClick={() => setOrgDropdownOpen(false)} />
      )}
    </div>
  );
}
