'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Activity, Menu, X } from 'lucide-react';
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
    <header className="sticky top-0 z-50 border-b border-white/10 bg-[#050909]/90 backdrop-blur-xl md:hidden">
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-3">
          <div className="grid h-8 w-8 place-items-center rounded-full border border-[#c8ff3d]/30 bg-[#c8ff3d]/10">
            <Activity className="h-4 w-4 text-[#c8ff3d]" />
          </div>
          <div><h1 className="text-sm font-semibold tracking-[0.22em] text-white">GERT</h1><p className="technical-label text-[8px] text-slate-500">Tail-risk intelligence</p></div>
        </div>
        <button aria-label={isOpen ? 'Close navigation' : 'Open navigation'} onClick={() => setIsOpen(!isOpen)} className="rounded-full border border-white/10 p-2 text-slate-300">
          {isOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>
      
      {isOpen && (
        <nav className="flex flex-col gap-1 px-4 pb-4">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setIsOpen(false)}
              className={clsx(
                "rounded-xl px-4 py-3 text-sm font-medium transition-colors",
                pathname === item.href ? "bg-white/10 text-[#c8ff3d]" : "text-slate-400"
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
