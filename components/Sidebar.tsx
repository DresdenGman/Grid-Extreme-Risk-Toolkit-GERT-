'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Activity, LayoutDashboard, CloudLightning, LineChart, History, BookOpen, Settings } from 'lucide-react';
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
    <aside className="w-64 bg-slate-950 border-r border-slate-800 flex-col hidden md:flex h-full">
      {/* Brand */}
      <div className="h-16 flex items-center px-6 border-b border-slate-800">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-3">
            <div className="bg-indigo-600 p-1.5 rounded text-white shadow-[0_0_15px_rgba(79,70,229,0.5)]">
              <Activity className="h-5 w-5" />
            </div>
            <span className="font-bold tracking-tight text-slate-100">
              GERT <span className="text-slate-600 text-xs font-normal align-top">v0.2</span>
            </span>
          </div>
          <div className="text-[10px] font-mono text-slate-500">
            {health
              ? `Model: ${health.backend} • Env: ${health.env} • AI: ${health.ai_enabled ? 'ON' : 'OFF'}`
              : 'Model: loading…'}
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-6 px-3 space-y-1">
        <div className="px-3 mb-2 text-xs font-bold text-slate-500 uppercase tracking-wider">
          Platform
        </div>
        {navItems.map((item) => {
          const isActive = item.href === '/' ? pathname === '/' : pathname.startsWith(item.href);
          const Icon = item.icon;
          
          return (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                "group flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-all duration-200",
                isActive
                  ? "bg-slate-900 text-indigo-400 border border-slate-800 shadow-sm"
                  : "text-slate-400 hover:bg-slate-900/50 hover:text-slate-200"
              )}
            >
              <Icon className={clsx("h-4 w-4", isActive ? "text-indigo-400" : "text-slate-500 group-hover:text-slate-300")} />
              {item.name}
              {isActive && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.8)]" />}
            </Link>
          );
        })}
      </nav>

      {/* Footer / Status */}
      <div className="p-4 border-t border-slate-800 bg-slate-950">
        <div className="flex items-center gap-3 px-2 py-2 rounded-md bg-slate-900/50 border border-slate-800/50">
          <div className="relative">
            <div className={`w-2 h-2 rounded-full ${isHealthy ? 'bg-emerald-500' : 'bg-amber-400'}`}></div>
            <div className={`absolute top-0 left-0 w-2 h-2 rounded-full opacity-75 ${isHealthy ? 'bg-emerald-500 animate-ping' : 'bg-amber-400 animate-ping'}`}></div>
          </div>
          <div className="flex flex-col">
            <span className="text-[10px] font-bold text-slate-400 uppercase">System Status</span>
            <span className={`text-xs font-mono ${isHealthy ? 'text-emerald-400' : 'text-amber-300'}`}>
              {health ? (isHealthy ? 'ONLINE' : health.status.toUpperCase()) : 'CHECKING'}
            </span>
            {health && (
              <span className="text-[10px] font-mono text-slate-500 mt-0.5">
                Backend: {health.backend} • Env: {health.env}
              </span>
            )}
          </div>
          <Settings className="ml-auto h-4 w-4 text-slate-600 hover:text-slate-400 cursor-pointer" />
        </div>
      </div>
    </aside>
  );
}