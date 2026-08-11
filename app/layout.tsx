import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import Navbar from "@/components/Navbar";
import { ToastProvider } from "@/components/ToastProvider";
import PresentationNotice from "@/components/PresentationNotice";
import React from "react";

export const metadata: Metadata = {
  title: "GERT — Grid Extreme Risk Intelligence",
  description: "Decision intelligence for power-system tail risk, capacity stress and extreme events.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="brs-frame flex h-screen overflow-hidden border-[8px] border-[#141414] selection:bg-[#ff4d00] selection:text-white">
        <ToastProvider>
          <Sidebar />
          <div className="min-w-0 flex-1 overflow-hidden">
            <Navbar />
            <main className="relative h-full overflow-y-auto overflow-x-hidden scrollbar-thin scrollbar-thumb-slate-800 scrollbar-track-transparent md:h-screen">
              <div className="mx-auto max-w-[1720px] px-4 py-5 sm:px-6 sm:py-7 xl:px-10 xl:py-9">
              <PresentationNotice />
              {children}
              </div>
            </main>
          </div>
        </ToastProvider>
      </body>
    </html>
  );
}
