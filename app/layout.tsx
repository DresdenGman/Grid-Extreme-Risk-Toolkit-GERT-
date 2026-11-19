import type { Metadata } from 'next';
import './globals.css';
import React from 'react';
import { PRODUCT_NAME } from '@/lib/citations';

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://gert-d.vercel.app';

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: PRODUCT_NAME,
  description: 'Explore historical ERCOT load, compare capacity assumptions, and reproduce grid-risk calculations with downloadable evidence.',
  applicationName: PRODUCT_NAME,
  icons: {
    icon: [
      { url: '/favicon.ico' },
      { url: '/favicon.svg', type: 'image/svg+xml' },
    ],
  },
  keywords: [
    'power grid risk',
    'ERCOT',
    'probabilistic forecasting',
    'extreme weather',
    'applied mathematics',
    'quantile modeling',
  ],
  authors: [{ name: 'Dresden Goehner' }],
  openGraph: {
    title: PRODUCT_NAME,
    description: 'Evidence-first decision support for power-system tail risk, capacity stress and extreme events.',
    images: [{ url: '/og.png', width: 1731, height: 909, alt: PRODUCT_NAME }],
  },
  twitter: {
    card: 'summary_large_image',
    title: PRODUCT_NAME,
    description: 'Evidence-first decision support for power-system tail risk, capacity stress and extreme events.',
    images: ['/og.png'],
  },
};

const softwareApplicationJsonLd = {
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: PRODUCT_NAME,
  applicationCategory: 'ScientificApplication',
  operatingSystem: 'Web',
  url: siteUrl,
  codeRepository: 'https://github.com/DresdenGman/Grid-Extreme-Risk-Toolkit-GERT-',
  description:
    'Evidence-first decision support for ERCOT power-grid tail risk, probabilistic load research, scenario stress testing and model-governance controls.',
  author: {
    '@type': 'Person',
    name: 'Dresden Goehner',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(softwareApplicationJsonLd) }}
        />
        {children}
      </body>
    </html>
  );
}
