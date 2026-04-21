import type { Metadata, Viewport } from 'next';
import type { ReactNode } from 'react';

export const metadata: Metadata = {
  title: {
    default: 'ozzb2b — B2B outsourcing marketplace',
    template: '%s — ozzb2b',
  },
  description:
    'Find outsourcing partners for IT, accounting, and legal work. Verified providers, transparent info, direct contact.',
  applicationName: 'ozzb2b',
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  themeColor: '#0f172a',
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body
        style={{
          margin: 0,
          fontFamily:
            'system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, sans-serif',
          background: '#0f172a',
          color: '#e2e8f0',
          minHeight: '100vh',
        }}
      >
        {children}
      </body>
    </html>
  );
}
