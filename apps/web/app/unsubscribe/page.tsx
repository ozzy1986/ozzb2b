import type { Metadata } from 'next';
import { UnsubscribeButton } from '@/components/UnsubscribeButton';

export const metadata: Metadata = {
  title: 'Отписка от писем',
  robots: { index: false, follow: false },
};

type SearchParams = { email?: string; token?: string };

export default async function UnsubscribePage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const { email, token } = await searchParams;
  return (
    <>
      <div className="hero">
        <h1>Отписка от писем</h1>
        <p>Мы пишем компаниям только когда к нам приходит подходящий запрос от клиента.</p>
      </div>
      {email && token ? (
        <UnsubscribeButton email={email} token={token} />
      ) : (
        <div className="empty">Ссылка неполная. Откройте её из письма целиком.</div>
      )}
    </>
  );
}
