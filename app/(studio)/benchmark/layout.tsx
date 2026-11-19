import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Benchmarks — GERT',
  description: 'The rejected v1.4 candidate: published gates, skill, and calibration. The production backtest stays locked.',
};

export default function BenchmarkLayout({ children }: { children: React.ReactNode }) {
  return children;
}
