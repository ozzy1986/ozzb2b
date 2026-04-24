import type { Metadata } from 'next';
import Link from 'next/link';
import {
  getAnalyticsSummary,
  getTopProviders,
  getTopSearches,
} from '@/lib/api';
import { humanizeError } from '@/lib/errors';
import type { AnalyticsSummary, TopProviders, TopQueries } from '@/lib/types';
import { authHeaders } from '@/lib/server-fetch';
import { requireAdmin } from '@/lib/auth-guard';

export const metadata: Metadata = {
  title: 'Аналитика',
  robots: { index: false, follow: false },
};

// Admin UI should always reflect the latest data.
export const revalidate = 0;
export const dynamic = 'force-dynamic';

type AdminSearchParams = { days?: string };

type FetchError = { kind: 'error'; message: string };
type FetchOk<T> = { kind: 'ok'; value: T };
type FetchResult<T> = FetchOk<T> | FetchError;

const EVENT_LABEL: Record<string, string> = {
  search_performed: 'Поиск',
  provider_viewed: 'Просмотр компании',
  chat_started: 'Начат диалог',
  chat_message_sent: 'Сообщение в чат',
};

async function guard<T>(p: Promise<T>): Promise<FetchResult<T>> {
  try {
    return { kind: 'ok', value: await p };
  } catch (err) {
    return { kind: 'error', message: humanizeError(err, 'admin-fetch') };
  }
}

export default async function AdminAnalyticsPage({
  searchParams,
}: {
  searchParams: Promise<AdminSearchParams>;
}) {
  const params = await searchParams;
  const days = Math.max(1, Math.min(365, Number.parseInt(params.days ?? '7', 10) || 7));

  await requireAdmin('/admin/analytics');

  const headers = await authHeaders();
  const init = { headers };

  const [summary, searches, providers] = await Promise.all([
    guard<AnalyticsSummary>(getAnalyticsSummary(days, init)),
    guard<TopQueries>(getTopSearches(days, 20, init)),
    guard<TopProviders>(getTopProviders(days, 20, init)),
  ]);

  return (
    <>
      <div className="hero">
        <h1>Аналитика</h1>
        <p>Ключевые продуктовые события за период.</p>
        <nav className="chips" aria-label="Период">
          {[1, 7, 30, 90].map((d) => (
            <Link
              key={d}
              href={`/admin/analytics?days=${d}`}
              className="chip"
              aria-current={d === days ? 'page' : undefined}
              style={d === days ? { background: '#0f172a', color: '#fff' } : undefined}
            >
              {d === 1 ? 'За сутки' : `${d} дней`}
            </Link>
          ))}
        </nav>
      </div>

      <section>
        <h2>Сводка по типам событий</h2>
        {summary.kind === 'error' ? (
          <div className="empty">{summary.message}</div>
        ) : summary.value.items.length === 0 ? (
          <div className="empty">Нет событий за выбранный период.</div>
        ) : (
          <table className="grid-table">
            <thead>
              <tr>
                <th>Событие</th>
                <th style={{ textAlign: 'right' }}>Количество</th>
              </tr>
            </thead>
            <tbody>
              {summary.value.items.map((r) => (
                <tr key={r.event_type}>
                  <td>{EVENT_LABEL[r.event_type] ?? r.event_type}</td>
                  <td style={{ textAlign: 'right' }}>{r.count.toLocaleString('ru-RU')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <div className="detail-grid" style={{ marginTop: 24 }}>
        <section>
          <h2>Популярные запросы</h2>
          {searches.kind === 'error' ? (
            <div className="empty">{searches.message}</div>
          ) : searches.value.items.length === 0 ? (
            <div className="empty">Поиск ещё никто не использовал за период.</div>
          ) : (
            <ol className="ranked-list">
              {searches.value.items.map((q, i) => (
                <li key={`${i}-${q.query}`}>
                  <span className="ranked-query">{q.query}</span>
                  <span className="ranked-count">{q.count}</span>
                </li>
              ))}
            </ol>
          )}
        </section>

        <section>
          <h2>Самые просматриваемые компании</h2>
          {providers.kind === 'error' ? (
            <div className="empty">{providers.message}</div>
          ) : providers.value.items.length === 0 ? (
            <div className="empty">Компании ещё никто не открывал за период.</div>
          ) : (
            <ol className="ranked-list">
              {providers.value.items.map((p) => (
                <li key={p.provider_id}>
                  <Link href={`/providers/${p.slug}`} className="ranked-query">
                    {p.display_name || p.slug}
                  </Link>
                  <span className="ranked-count">{p.count}</span>
                </li>
              ))}
            </ol>
          )}
        </section>
      </div>
    </>
  );
}
