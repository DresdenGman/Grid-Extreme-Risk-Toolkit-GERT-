import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Event replay — GERT',
  description: 'A labeled educational reconstruction. It is not an official historical record, and a failed fetch is left unavailable.',
};

export default function EventReplayLayout({ children }: { children: React.ReactNode }) {
  return children;
}
