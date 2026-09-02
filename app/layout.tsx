import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import Navbar from "@/components/Navbar";
import { ToastProvider } from "@/components/ToastProvider";
import PresentationNotice from "@/components/PresentationNotice";
import React from "react";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "https://gert-d.vercel.app";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: "GERT — Grid Extreme Risk Intelligence",
  description: "Decision intelligence for power-system tail risk, capacity stress and extreme events.",
  applicationName: "GERT",
  keywords: [
    "power grid risk",
    "ERCOT",
    "probabilistic forecasting",
    "extreme weather",
    "applied mathematics",
    "quantile modeling",
  ],
  authors: [{ name: "Dresden Goehner" }],
  openGraph: {
    title: "GERT — Grid Extreme Risk Intelligence",
    description: "Applied-mathematics decision intelligence for power-system tail risk, capacity stress and extreme events.",
    images: [{ url: "/og.png", width: 1731, height: 909, alt: "GERT — Grid Extreme Risk Intelligence" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "GERT — Grid Extreme Risk Intelligence",
    description: "Applied-mathematics decision intelligence for power-system tail risk, capacity stress and extreme events.",
    images: ["/og.png"],
  },
};

const softwareApplicationJsonLd = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: "GERT — Grid Extreme Risk Toolkit",
  applicationCategory: "ScientificApplication",
  operatingSystem: "Web",
  url: siteUrl,
  codeRepository: "https://github.com/DresdenGman/Grid-Extreme-Risk-Toolkit-GERT-",
  description:
    "Evidence-first decision support for ERCOT power-grid tail risk, probabilistic load research, scenario stress testing and model-governance controls.",
  author: {
    "@type": "Person",
    name: "Dresden Goehner",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="brs-frame flex h-screen overflow-hidden border-[8px] border-[#141414] selection:bg-[#ff4d00] selection:text-white">
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(softwareApplicationJsonLd) }}
        />
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
