import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Scenario lab — GERT',
  description: 'Scenario analysis stays gated until a model is validated. The page does not fill in a forecast.',
};

export default function ScenarioLayout({ children }: { children: React.ReactNode }) {
  return children;
}
