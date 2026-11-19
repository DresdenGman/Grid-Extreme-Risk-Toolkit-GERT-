import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Historical Lab — GERT',
  description: 'A deterministic teaching exercise on three recorded ERCOT windows. It is not a forecast or a representative backtest.',
};

export default function HistoryLayout({ children }: { children: React.ReactNode }) {
  return children;
}
