import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import React from "react";

export const metadata: Metadata = {
  title: "Grid Extreme Risk Toolkit",
  description: "Quantile Regression & EVT Analysis Engine",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="font-sans text-slate-300 bg-slate-950 flex h-screen overflow-hidden selection:bg-indigo-500/30">
        {/* Fixed Sidebar */}
        <Sidebar />
        
        {/* Main Scrollable Area */}
        <main className="flex-1 overflow-y-auto overflow-x-hidden relative scrollbar-thin scrollbar-thumb-slate-800 scrollbar-track-transparent">
          <div className="max-w-[1600px] mx-auto px-6 py-8">
            {children}
          </div>
        </main>
      </body>
    </html>
  );
}