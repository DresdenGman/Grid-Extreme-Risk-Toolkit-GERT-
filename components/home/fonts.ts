import localFont from 'next/font/local';

export const plexSans = localFont({
  src: '../../assets/fonts/ibm-plex-sans.woff2',
  weight: '400 700',
  display: 'swap',
  variable: '--font-plex-sans',
});

export const plexMono = localFont({
  src: [
    { path: '../../assets/fonts/ibm-plex-mono-400.woff2', weight: '400', style: 'normal' },
    { path: '../../assets/fonts/ibm-plex-mono-600.woff2', weight: '600', style: 'normal' },
  ],
  display: 'swap',
  variable: '--font-plex-mono',
});

export const sourceSerif = localFont({
  src: [
    { path: '../../assets/fonts/source-serif-4-400.woff2', weight: '400', style: 'normal' },
    { path: '../../assets/fonts/source-serif-4-400-italic.woff2', weight: '400', style: 'italic' },
  ],
  display: 'swap',
  variable: '--font-source-serif',
});

export const homeFonts = {
  sans: plexSans.style.fontFamily,
  serif: sourceSerif.style.fontFamily,
  mono: plexMono.style.fontFamily,
};
