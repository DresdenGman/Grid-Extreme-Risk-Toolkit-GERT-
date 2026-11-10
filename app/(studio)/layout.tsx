import Sidebar from '@/components/Sidebar';
import Navbar from '@/components/Navbar';
import { ToastProvider } from '@/components/ToastProvider';
import PresentationNotice from '@/components/PresentationNotice';

export default function StudioLayout({ children }: { children: React.ReactNode }) {
  return (
    <ToastProvider>
      <div className="brs-frame flex h-screen overflow-hidden border-[8px] border-[#141414] selection:bg-[#ff4d00] selection:text-white">
        <Sidebar />
        <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
          <Navbar />
          <main className="relative min-h-0 flex-1 overflow-y-auto overflow-x-hidden scrollbar-thin scrollbar-thumb-slate-800 scrollbar-track-transparent">
            <div className="mx-auto max-w-[1720px] px-4 py-5 sm:px-6 sm:py-7 xl:px-10 xl:py-9">
              <PresentationNotice />
              {children}
            </div>
          </main>
        </div>
      </div>
    </ToastProvider>
  );
}
