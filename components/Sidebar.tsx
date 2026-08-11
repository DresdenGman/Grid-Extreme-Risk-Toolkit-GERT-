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

  useEffect(() => {
    let cancelled = false;
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
    <aside className="hidden h-full w-[276px] shrink-0 flex-col border-r border-white/[0.08] bg-[#070c0c]/90 backdrop-blur-xl md:flex">
      <div className="flex min-h-24 items-center border-b border-white/[0.08] px-6">
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-3.5">
            <div className="grid h-10 w-10 place-items-center rounded-full border border-[#c8ff3d]/25 bg-[#c8ff3d]/10 text-[#c8ff3d] shadow-[0_0_24px_rgba(200,255,61,0.08)]">
              <Activity className="h-5 w-5" />
            </div>
            <div>
              <span className="block text-sm font-semibold tracking-[0.24em] text-white">GERT</span>
              <span className="technical-label text-[8px] text-slate-500">Grid extreme risk toolkit</span>
            </div>
          </div>
          <div className="technical-label pl-[54px] text-[8px] text-slate-600">
            {health
              ? `Model: ${health.backend} • Env: ${health.env} • AI: ${health.ai_enabled ? 'ON' : 'OFF'}`
              : 'Model: loading…'}
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-7">
        <div className="technical-label mb-3 px-3 text-slate-600">
          Decision workflow
        </div>
        {navItems.map((item) => {
          const isActive = item.href === '/' ? pathname === '/' : pathname.startsWith(item.href);
          const Icon = item.icon;
          
          return (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                "group flex items-center gap-3 rounded-xl border px-3 py-3 text-sm font-medium transition-all duration-200",
                isActive
                  ? "border-[#c8ff3d]/15 bg-[#c8ff3d]/[0.07] text-white"
                  : "border-transparent text-slate-500 hover:border-white/[0.06] hover:bg-white/[0.03] hover:text-slate-200"
              )}
            >
              <Icon className={clsx("h-4 w-4", isActive ? "text-[#c8ff3d]" : "text-slate-600 group-hover:text-slate-300")} />
              {item.name}
              {isActive && <ArrowUpRight className="ml-auto h-3.5 w-3.5 text-[#c8ff3d]" />}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-white/[0.08] p-4">
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.025] p-4">
          <div className="mb-3 flex items-center gap-3">
          <div className="relative">
            <div className={`h-2 w-2 rounded-full ${isHealthy ? 'signal-dot bg-[#c8ff3d]' : 'bg-amber-400'}`}></div>
          </div>
          <div className="flex flex-1 items-center justify-between">
            <span className="technical-label text-slate-500">System</span>
            <span className={`technical-label ${isHealthy ? 'text-[#c8ff3d]' : 'text-amber-300'}`}>
              {health ? (isHealthy ? 'ONLINE' : health.status.toUpperCase()) : 'CHECKING'}
            </span>
          </div>
          </div>
          <div className="grid grid-cols-2 gap-2 border-t border-white/[0.07] pt-3 text-[10px]">
            <span className="text-slate-600">MODEL</span><span className="truncate text-right font-mono text-slate-400">{health?.backend ?? '—'}</span>
            <span className="text-slate-600">ENV</span><span className="truncate text-right font-mono text-slate-400">{health?.env ?? '—'}</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
