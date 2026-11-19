import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Live monitor — GERT',
  description: 'ERCOT weather and grid context when a source is an external forecast or official. Prediction stays gated, and missing values stay unavailable.',
};

export default function MonitorLayout({ children }: { children: React.ReactNode }) {
  return children;
}
