import type { Metadata } from 'next';
import Link from '@/components/AppLink';
import { listLeads } from '@/lib/api';
import { humanizeError } from '@/lib/errors';
import { requireAdmin } from '@/lib/auth-guard';
import { authHeaders } from '@/lib/server-fetch';
import { trCategory, trCity } from '@/lib/ru';
import { LEAD_STATUS_LABEL } from '@/lib/leads';
import type { LeadSummary } from '@/lib/types';

export const metadata: Metadata = {
  title: 'Заявки',
  robots: { index: false, follow: false },
};

export const revalidate = 0;
export const dynamic = 'force-dynamic';

export default async function AdminLeadsPage() {
  await requireAdmin('/admin/leads');
  const headers = await authHeaders();

  let leads: LeadSummary[] = [];
  let error: string | null = null;
  try {
    leads = await listLeads({ headers });
  } catch (err) {
    error = humanizeError(err, 'admin-fetch');
  }

  return (
    <>
      <div className="hero">
        <h1>Заявки</h1>
        <p>Запросы клиентов и черновики писем подрядчикам. Письма уходят только после проверки.</p>
      </div>
      {error ? (
        <div className="empty">{error}</div>
      ) : leads.length === 0 ? (
        <div className="empty">Заявок пока нет.</div>
      ) : (
        <table className="grid-table">
          <thead>
            <tr>
              <th>Дата</th>
              <th>Услуга</th>
              <th>Клиент</th>
              <th>Статус</th>
              <th style={{ textAlign: 'right' }}>Черновики / отправлено</th>
            </tr>
          </thead>
          <tbody>
            {leads.map((lead) => (
              <tr key={lead.id}>
                <td>
                  <Link href={`/admin/leads/${lead.id}`}>
                    {new Date(lead.created_at).toLocaleString('ru-RU')}
                  </Link>
                </td>
                <td>
                  {lead.category_slug
                    ? trCategory(lead.category_slug, lead.category_name ?? '')
                    : '—'}
                  {lead.city_name ? `, ${trCity(lead.city_name)}` : ''}
                </td>
                <td>
                  {lead.contact_name}
                  {lead.company_name ? ` (${lead.company_name})` : ''}
                </td>
                <td>{LEAD_STATUS_LABEL[lead.status]}</td>
                <td style={{ textAlign: 'right' }}>
                  {lead.drafts} / {lead.sent}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
