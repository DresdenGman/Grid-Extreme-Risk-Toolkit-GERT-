'use client';

import Link from 'next/link';
import { useEffect, useId, useRef, useState } from 'react';
import { toolIndex } from '@/lib/homepage/tools';
import styles from './home.module.css';

export function ToolsMenu() {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLAnchorElement>(null);
  const menuId = useId();

  useEffect(() => {
    if (!open) return undefined;
    function onPointerDown(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    }
    function onKey(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setOpen(false);
        buttonRef.current?.focus();
      }
    }
    document.addEventListener('mousedown', onPointerDown);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onPointerDown);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  function links(): HTMLAnchorElement[] {
    return Array.from(rootRef.current?.querySelectorAll<HTMLAnchorElement>('[data-tool-link]') ?? []);
  }

  function move(current: EventTarget | null, direction: 1 | -1 | 'first' | 'last') {
    const items = links();
    if (!items.length) return;
    const index = items.indexOf(current as HTMLAnchorElement);
    const next = direction === 'first'
      ? items[0]
      : direction === 'last'
        ? items[items.length - 1]
        : items[(index + direction + items.length) % items.length];
    next?.focus();
    if (typeof next?.scrollIntoView === 'function') next.scrollIntoView({ block: 'nearest' });
  }

  function onButtonKeyDown(event: React.KeyboardEvent<HTMLAnchorElement>) {
    if (event.key !== 'ArrowDown' && event.key !== 'ArrowUp') return;
    event.preventDefault();
    setOpen(true);
    requestAnimationFrame(() => move(null, event.key === 'ArrowUp' ? 'last' : 'first'));
  }

  function onMenuKeyDown(event: React.KeyboardEvent<HTMLDivElement>) {
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      move(event.target, 1);
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      move(event.target, -1);
    } else if (event.key === 'Home') {
      event.preventDefault();
      move(null, 'first');
    } else if (event.key === 'End') {
      event.preventDefault();
      move(null, 'last');
    }
  }

  return (
    <div className={styles.tools} ref={rootRef}>
      <a
        ref={buttonRef}
        href="#tools"
        className={open ? styles.toolsOpen : undefined}
        aria-expanded={open}
        aria-controls={menuId}
        onClick={(event) => {
          event.preventDefault();
          setOpen((value) => !value);
        }}
        onKeyDown={onButtonKeyDown}
      >
        Tools
      </a>
      {open ? (
        <div
          id={menuId}
          className={styles.toolsMenu}
          role="group"
          aria-label="Tools"
          onKeyDown={onMenuKeyDown}
        >
          {toolIndex.map((group) => (
            <div key={group.id} className={styles.menuGroup}>
              <div className={styles.menuLabel}>{group.label}</div>
              <ul>
                {group.entries.map((entry) => (
                  <li key={entry.href}>
                    <Link href={entry.href} data-tool-link="" onClick={() => setOpen(false)}>
                      {entry.name}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
          <div className={styles.menuGroup}>
            <a href="#tools" data-tool-link="" onClick={() => setOpen(false)}>
              Full index
            </a>
          </div>
        </div>
      ) : null}
    </div>
  );
}
