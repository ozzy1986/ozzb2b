import type { Metadata, Viewport } from 'next';
import { Onest } from 'next/font/google';
import Link from '@/components/AppLink';
import type { ReactNode } from 'react';
import { SiteNav } from '@/components/SiteNav';
import './globals.css';

// Onest: a calm modern grotesque drawn for Cyrillic first.
const onest = Onest({
  subsets: ['latin', 'cyrillic'],
  weight: ['400', '500', '600'],
  display: 'swap',
  variable: '--font-onest',
});

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
  themeColor: '#f3f5f2',
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ru" className={onest.variable}>
      <body>
        <header className="site-header">
          <div className="container header-inner">
            <Link href="/" className="brand">
              <BrandMark />
              <span>ozzb2b</span>
            </Link>
            <SiteNav />
          </div>
        </header>
        <main className="container site-main">{children}</main>
        <footer className="site-footer">
          <div className="container footer-inner">
            <div>
              <Link href="/" className="brand">
                <BrandMark />
                <span>ozzb2b</span>
              </Link>
              <p>Соединяем бизнес с подрядчиками, которые ему действительно подходят.</p>
            </div>
            <nav className="footer-col" aria-label="Каталог">
              <h4>Каталог</h4>
              <Link href="/providers">Компании</Link>
              <Link href="/categories">Категории</Link>
              <Link href="/request">Оставить заявку</Link>
            </nav>
            <nav className="footer-col" aria-label="Подрядчикам">
              <h4>Подрядчикам</h4>
              <Link href="/register">Регистрация</Link>
              <Link href="/login">Вход</Link>
              <Link href="/sitemap.xml">Карта сайта</Link>
            </nav>
          </div>
          <div className="container footer-bottom">© {new Date().getFullYear()} ozzb2b</div>
        </footer>
      </body>
    </html>
  );
}

/** Two overlapping rings: two companies meeting. */
function BrandMark() {
  return (
    <span className="brand-mark" aria-hidden>
      <svg width="26" height="26" viewBox="0 0 26 26" fill="none">
        <circle cx="9.5" cy="13" r="6.75" stroke="currentColor" strokeWidth="2.5" />
        <circle cx="16.5" cy="13" r="6.75" stroke="currentColor" strokeWidth="2.5" opacity="0.55" />
      </svg>
    </span>
  );
}
