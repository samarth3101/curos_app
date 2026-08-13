import Link from 'next/link';
import Image from 'next/image';
import { Button } from '@/components/ui/button';

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50 p-4">
      <div className="flex flex-col items-center text-center space-y-6 max-w-lg">
        
        <div className="flex items-center justify-center mb-2">
          <Image src="/curos_logo.png" alt="Curos Logo" width={64} height={64} className="h-16 w-auto object-contain" />
        </div>
        
        <h1 className="text-3xl font-bold tracking-tight text-gray-900">
          Cortex <span className="text-red-600">OI</span>
        </h1>
        
        <div className="space-y-2">
          <h2 className="text-xl font-semibold text-gray-700">Page under construction</h2>
          <p className="text-gray-500">
            You&apos;ve reached a section of the application that is not yet fully implemented or the page you are looking for does not exist.
            Cortex OI is constantly evolving with new modules.
          </p>
        </div>
        
        <div className="pt-6">
          <Link href="/">
            <Button size="lg" className="px-8">
              Return to Dashboard
            </Button>
          </Link>
        </div>

      </div>
    </div>
  );
}
