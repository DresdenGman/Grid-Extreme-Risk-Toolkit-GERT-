'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Dashboard() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/');
  }, [router]);

  return (
    <div className="flex h-screen w-full items-center justify-center bg-slate-950">
      <div className="text-sm text-slate-500 animate-pulse">Redirecting to Live Monitor...</div>
    </div>
  );
}