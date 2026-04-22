import { freshnessLabel } from '@/lib/ru';

export function FreshnessBadge({ lastScrapedAt }: { lastScrapedAt: string | null }) {
  const label = freshnessLabel(lastScrapedAt);
  if (!label) return null;
  return (
    <span className="chip" title={`Данные обновлены: ${lastScrapedAt}`}>
      {label}
    </span>
  );
}
