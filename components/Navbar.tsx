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
  { name: 'Method', href: '/about' },
  { name: 'Research', href: '/research' },
];

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 border-b border-[#141414] bg-[#e4e3e0]/95 backdrop-blur-xl md:hidden">
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-3">
          <div className="grid h-8 w-8 place-items-center border border-[#141414] bg-[#141414]">
            <Activity className="h-4 w-4 text-[#ff4d00]" />
          </div>
          <div><h1 className="display-serif text-lg text-[#141414]">GERT</h1><p className="technical-label text-[8px] text-[#6d6b66]">Tail-risk intelligence</p></div>
        </div>
        <button aria-label={isOpen ? 'Close navigation' : 'Open navigation'} onClick={() => setIsOpen(!isOpen)} className="border border-[#141414] p-2 text-[#141414]">
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
                "border px-4 py-3 text-sm font-medium transition-colors",
                pathname === item.href ? "border-[#141414] bg-[#141414] text-[#e4e3e0]" : "border-transparent text-[#5f5d58]"
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
