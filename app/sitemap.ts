import type { MetadataRoute } from 'next';

const routes = [
  '',
  '/scenario',
  '/benchmark',
  '/events/polar-vortex',
  '/about',
  '/research',
];

export default function sitemap(): MetadataRoute.Sitemap {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://gert-d.vercel.app';
  const lastModified = new Date('2026-08-30T00:00:00.000Z');

  return routes.map((route) => ({
    url: `${siteUrl}${route}`,
    lastModified,
    changeFrequency: route === '' ? 'daily' : 'monthly',
    priority: route === '' ? 1 : route === '/benchmark' || route === '/research' ? 0.9 : 0.8,
  }));
}
