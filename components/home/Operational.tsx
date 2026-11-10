'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import { interpretLive, type LiveView } from '@/lib/homepage/live';
import styles from './home.module.css';

const LiveContext = createContext<LiveView>(interpretLive(null, null));

async function readJson(url: string, signal: AbortSignal): Promise<unknown> {
  try {
    const response = await fetch(url, { cache: 'no-store', signal });
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

export function OperationalProvider({ children }: { children: React.ReactNode }) {
  const [view, setView] = useState<LiveView>(() => interpretLive(null, null));

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      readJson('/api/gert/weather/live?region=ERCOT_SYSTEM', controller.signal),
      readJson('/api/gert/load/current?region=ERCOT_SYSTEM', controller.signal),
    ]).then(([weather, load]) => {
      if (!controller.signal.aborted) setView(interpretLive(weather, load));
    });
    return () => controller.abort();
  }, []);

  return <LiveContext.Provider value={view}>{children}</LiveContext.Provider>;
}

function useLive() {
  return useContext(LiveContext);
}

export function AsOf() {
  const live = useLive();
  return (
    <div className={styles.asof}>
      As of {live.asOfLabel}
      <br />
      (America/Chicago)
    </div>
  );
}

export function HeroFoot({ closer }: { closer: string }) {
  const live = useLive();
  return (
    <div className={styles.heroFoot}>
      <div className={styles.live}>{live.foot}</div>
      <div className={styles.closer}>{closer}</div>
    </div>
  );
}

function Fact({ label, value, detail, live }: { label: string; value: string; detail: string | null; live: boolean }) {
  return (
    <>
      <div className={styles.factLabel}>{label}</div>
      <div className={live ? styles.valLive : styles.val}>{value}</div>
      {detail ? <div className={styles.detail}>{detail}</div> : null}
    </>
  );
}

export function Facts() {
  const live = useLive();
  return (
    <div className={styles.facts} aria-live="polite">
      <Fact label="Weather" value={live.weather} detail={live.weatherDetail} live={live.weatherLive} />
      <Fact label="System load" value={live.load} detail={live.loadDetail} live={live.loadLive} />
      <Fact label="Capacity" value={live.capacity} detail={live.capacityDetail} live={live.capacityLive} />
    </div>
  );
}
