"use client";

import { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/authStore';
import { useOrgStore } from '@/stores/orgStore';
import { authService } from '@/services/auth';
import { organizationsService } from '@/services/organizations';
import { normalizeApiError } from '@/lib/errors';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const setAuth = useAuthStore((state) => state.setAuth);
  const { setOrganizations } = useOrgStore();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const tokens = await authService.login({ email, password });
      
      // Temporarily store tokens to allow fetching /me
      useAuthStore.setState({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token });
      
      // Fetch user profile
      const user = await authService.getMe();
      
      // Save all to store
      setAuth(tokens.access_token, tokens.refresh_token, user);
      
      // Fetch user's organizations and set them
      try {
        const orgs = await organizationsService.list();
        if (orgs.length === 0) {
          // No organizations yet — send to onboarding
          router.push('/onboarding');
        } else {
          setOrganizations(orgs);
          router.push('/');
        }
      } catch {
        // If org fetch fails, still go to dashboard — they can create from there
        router.push('/');
      }
    } catch (err) {
      setError(normalizeApiError(err));
      useAuthStore.setState({ accessToken: null, refreshToken: null });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          <div className="flex justify-center mb-4">
            <Image src="/curos_logo.png" alt="Curos Logo" width={100} height={48} className="h-12 w-auto object-contain" />
          </div>
          <CardTitle className="text-2xl font-bold tracking-tight">Cortex <span className="text-red-600">OI</span></CardTitle>
          <CardDescription>Enter your credentials to access the operational dashboard</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-4">
            {error && <div className="rounded-md bg-red-50 p-3 text-sm text-red-600">{error}</div>}
            
            <div className="space-y-2">
              <label className="text-sm font-medium leading-none" htmlFor="login-email">Email</label>
              <Input
                id="login-email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium leading-none" htmlFor="login-password">Password</label>
              <Input
                id="login-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Signing in...' : 'Sign In'}
            </Button>

            <p className="text-center text-sm text-gray-500">
              Don&apos;t have an account?{' '}
              <Link href="/signup" className="font-medium text-blue-600 hover:text-blue-500">
                Sign up
              </Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
