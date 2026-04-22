import type { Metadata, Viewport } from 'next';
import Link from 'next/link';
import type { ReactNode } from 'react';
import { SiteNav } from '@/components/SiteNav';
import './globals.css';

export const metadata: Metadata = {
  metadataBase: new URL('https://ozzb2b.com'),
  title: {
    default: 'ozzb2b — маркетплейс B2B-исполнителей',
    template: '%s — ozzb2b',
  },
  description:
    'Платформа для поиска проверенных B2B-подрядчиков в России: ИТ, бухгалтерия, юридические и маркетинговые услуги.',
  applicationName: 'ozzb2b',
  robots: { index: true, follow: true },
  openGraph: {
    type: 'website',
    siteName: 'ozzb2b',
    url: 'https://ozzb2b.com',
  },
};

export const viewport: Viewport = {
  themeColor: '#0f172a',
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ru">
      <body>
        <header className="site-header">
          <div className="container header-inner">
            <Link href="/" className="brand">
              <span className="brand-mark" aria-hidden>◎</span>
              <span>ozzb2b</span>
            </Link>
            <SiteNav />
          </div>
        </header>
        <main className="container site-main">{children}</main>
        <footer className="site-footer">
          <div className="container footer-inner">
            <span>© {new Date().getFullYear()} ozzb2b</span>
            <span>
              <Link href="/sitemap.xml">карта сайта</Link> · <Link href="/robots.txt">robots</Link>
            </span>
          </div>
        </footer>
      </body>
    </html>
  );
}
