import { JournalFrame } from '@/components/journal/JournalFrame';

export default function StudioLayout({ children }: { children: React.ReactNode }) {
  return <JournalFrame>{children}</JournalFrame>;
}
