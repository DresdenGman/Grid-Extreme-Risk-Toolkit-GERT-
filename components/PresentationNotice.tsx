'use client';

import { useEffect, useState } from 'react';

export default function PresentationNotice() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    setVisible(new URLSearchParams(window.location.search).get('demo') === '1');
  }, []);

  if (!visible) return null;

  return (
    <div className="mb-5 flex flex-col gap-3 border border-[#141414] bg-[#141414] px-5 py-4 text-[#e4e3e0] shadow-[5px_5px_0_#ff4d00] sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-3">
        <span className="technical-label border border-[#ff4d00] bg-[#ff4d00] px-2.5 py-1 text-[#141414]">Presentation mode</span>
        <span className="text-xs text-[#c8c6c0]">Simulated ERCOT decision snapshot · No live operational claims</span>
      </div>
      <a href="/" className="technical-label text-[#ff7a42] transition hover:text-white">Exit demo →</a>
    </div>
  );
}
