'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Activity, LayoutDashboard, CloudLightning, LineChart, History, BookOpen, ArrowUpRight } from 'lucide-react';
import { clsx } from 'clsx';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { HealthStatus } from '@/lib/types';

const navItems = [
  { name: 'Live Monitor', href: '/', icon: LayoutDashboard },
  { name: 'Scenario Lab', href: '/scenario', icon: CloudLightning },
  { name: 'Benchmarks', href: '/benchmark', icon: LineChart },
  { name: 'Event Replay', href: '/events/polar-vortex', icon: History },
  { name: 'Methodology', href: '/about', icon: BookOpen },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [presentationMode, setPresentationMode] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setPresentationMode(new URLSearchParams(window.location.search).get('demo') === '1');
    api.health()
      .then((env) => {
        if (!cancelled) setHealth(env.data);
      })
      .catch((e) => console.warn('Health check failed', e));
    return () => {
      cancelled = true;
    };
  }, []);

  const isHealthy = health?.status === 'ok';

  return (
    <aside className="hidden h-full w-[276px] shrink-0 flex-col border-r border-[#141414] bg-[#e4e3e0] md:flex">
      <div className="flex min-h-24 items-center border-b border-[#141414] px-6">
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-3.5">
            <div className="grid h-10 w-10 place-items-center border border-[#141414] bg-[#141414] text-[#ff4d00] shadow-[4px_4px_0_#ff4d00]">
              <Activity className="h-5 w-5" />
            </div>
            <div>
              <span className="display-serif block text-xl text-[#141414]">GERT</span>
              <span className="technical-label text-[8px] text-[#6d6b66]">Grid extreme risk toolkit</span>
            </div>
          </div>
          <div className="technical-label pl-[54px] text-[8px] text-[#87847e]">
            {presentationMode
              ? 'Model: tail-qrf.demo • Presentation'
              : health
              ? `Model: ${health.backend} • Env: ${health.env} • AI: ${health.ai_enabled ? 'ON' : 'OFF'}`
              : 'Model: loading…'}
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-7">
        <div className="technical-label mb-3 px-3 text-[#87847e]">
          Decision workflow
        </div>
        {navItems.map((item) => {
          const isActive = item.href === '/' ? pathname === '/' : pathname.startsWith(item.href);
          const Icon = item.icon;
          
          return (
            <Link
              key={item.href}
              href={presentationMode ? `${item.href}?demo=1` : item.href}
              className={clsx(
                "group flex items-center gap-3 border px-3 py-3 text-sm font-medium transition-all duration-200",
                isActive
                  ? "border-[#141414] bg-[#141414] text-[#e4e3e0] shadow-[4px_4px_0_#ff4d00]"
                  : "border-transparent text-[#5f5d58] hover:border-[#141414] hover:bg-[#d9d8d4] hover:text-[#141414]"
              )}
            >
              <Icon className={clsx("h-4 w-4", isActive ? "text-[#ff4d00]" : "text-[#87847e] group-hover:text-[#141414]")} />
              {item.name}
              {isActive && <ArrowUpRight className="ml-auto h-3.5 w-3.5 text-[#ff4d00]" />}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-[#141414] p-4">
        <div className="border border-[#141414] bg-[#deddd9] p-4 shadow-[4px_4px_0_#141414]">
          <div className="mb-3 flex items-center gap-3">
          <div className="relative">
            <div className={`h-2 w-2 ${isHealthy ? 'signal-dot bg-[#ff4d00]' : 'bg-amber-500'}`}></div>
          </div>
          <div className="flex flex-1 items-center justify-between">
            <span className="technical-label text-[#6d6b66]">System</span>
            <span className={`technical-label ${isHealthy ? 'text-[#ff4d00]' : 'text-amber-700'}`}>
              {health ? (presentationMode ? 'SIMULATED' : isHealthy ? 'ONLINE' : health.status.toUpperCase()) : 'CHECKING'}
            </span>
          </div>
          </div>
          <div className="grid grid-cols-2 gap-2 border-t border-black/20 pt-3 text-[10px]">
            <span className="text-[#87847e]">MODEL</span><span className="truncate text-right font-mono text-[#454545]">{health?.backend ?? '—'}</span>
            <span className="text-[#87847e]">ENV</span><span className="truncate text-right font-mono text-[#454545]">{health?.env ?? '—'}</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
