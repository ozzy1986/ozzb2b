import { getApiHealth } from '@/lib/api';

export const dynamic = 'force-dynamic';

export default async function HomePage() {
  const health = await getApiHealth();

  return (
    <main
      style={{
        display: 'flex',
        minHeight: '100vh',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px',
      }}
    >
      <section
        style={{
          maxWidth: 760,
          width: '100%',
          padding: 28,
          border: '1px solid #334155',
          borderRadius: 12,
          background: '#111827',
          boxShadow: '0 8px 32px rgba(0,0,0,0.2)',
        }}
      >
        <h1 style={{ marginTop: 0, fontSize: 28, letterSpacing: -0.5 }}>
          ozzb2b is online
        </h1>
        <p style={{ lineHeight: 1.6, margin: '8px 0 16px' }}>
          B2B outsourcing marketplace — IT, accounting, legal. Scaffolded. More coming soon.
        </p>
        <dl style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '4px 12px', margin: 0 }}>
          <dt style={{ opacity: 0.7 }}>Web</dt>
          <dd style={{ margin: 0 }}>Next.js SSR</dd>
          <dt style={{ opacity: 0.7 }}>API status</dt>
          <dd style={{ margin: 0 }}>
            {health.ok ? `ok (v${health.version ?? '?'})` : `unreachable: ${health.error}`}
          </dd>
        </dl>
      </section>
    </main>
  );
}
