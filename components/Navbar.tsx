'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Activity, Menu } from 'lucide-react';
import { useState } from 'react';
import { clsx } from 'clsx';

const navItems = [
  { name: 'Dashboard', href: '/' },
  { name: 'Scenario', href: '/scenario' },
  { name: 'Benchmark', href: '/benchmark' },
  { name: 'Events', href: '/events/polar-vortex' },
];

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const pathname = usePathname();

  return (
    <header className="md:hidden border-b border-slate-800 bg-slate-950 sticky top-0 z-50">
      <div className="px-6 py-4 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <Activity className="h-6 w-6 text-indigo-500" />
          <h1 className="text-lg font-bold text-slate-100">GERT</h1>
        </div>
        <button onClick={() => setIsOpen(!isOpen)} className="text-slate-400">
          <Menu className="h-6 w-6" />
        </button>
      </div>
      
      {isOpen && (
        <nav className="px-6 pb-4 flex flex-col gap-2">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setIsOpen(false)}
              className={clsx(
                "px-4 py-3 rounded-md text-sm font-medium transition-colors",
                pathname === item.href ? "bg-slate-900 text-indigo-400" : "text-slate-400"
              )}
            >
              {item.name}
            </Link>
          ))}
        </nav>
      )}
    </header>
  );
}