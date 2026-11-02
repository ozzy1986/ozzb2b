import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from '@/components/AppLink';
import { ApiError, getLead } from '@/lib/api';
import { humanizeError } from '@/lib/errors';
import { requireAdmin } from '@/lib/auth-guard';
import { authHeaders } from '@/lib/server-fetch';
import { trCategory, trCity } from '@/lib/ru';
import { LeadReview } from '@/components/LeadReview';
import type { LeadDetail } from '@/lib/types';

export const metadata: Metadata = {
  title: 'Заявка',
  robots: { index: false, follow: false },
};

export const revalidate = 0;
export const dynamic = 'force-dynamic';

export default async function AdminLeadPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  await requireAdmin(`/admin/leads/${id}`);
  const headers = await authHeaders();

  let lead: LeadDetail;
  try {
    lead = await getLead(id, { headers });
  } catch (err) {
    if (err instanceof ApiError && (err.status === 404 || err.status === 422)) notFound();
    return <div className="empty">{humanizeError(err, 'admin-fetch')}</div>;
  }

  return (
    <>
      <div className="hero">
        <p>
          <Link href="/admin/leads">← Все заявки</Link>
        </p>
        <h1>
          {lead.category_slug ? trCategory(lead.category_slug, lead.category_name ?? '') : 'Заявка'}
        </h1>
        <p>
          {new Date(lead.created_at).toLocaleString('ru-RU')}
          {lead.city_name ? ` · ${trCity(lead.city_name)}` : ' · город не важен'}
          {lead.budget ? ` · бюджет: ${lead.budget}` : ''}
        </p>
      </div>
      <LeadReview initial={lead} />
    </>
  );
}
