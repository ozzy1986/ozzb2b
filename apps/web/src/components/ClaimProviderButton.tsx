import Link from 'next/link';

type Props = {
  providerSlug: string;
  isClaimed: boolean;
};

/** Inline "Это моя компания" CTA shown on the provider detail page. */
export function ClaimProviderButton({ providerSlug, isClaimed }: Props) {
  if (isClaimed) {
    return (
      <div className="sidebar-card">
        <h3>Это ваша компания?</h3>
        <p className="auth-hint" style={{ marginTop: 0 }}>
          Эта компания уже подтверждена владельцем. Если это вы — войдите в свой кабинет.
        </p>
      </div>
    );
  }
  return (
    <div className="sidebar-card">
      <h3>Это моя компания</h3>
      <p className="auth-hint" style={{ marginTop: 0 }}>
        Подтвердите владение: разместите короткий meta-тег на главной странице сайта —
        и получите доступ к редактированию карточки и входящим чатам.
      </p>
      <Link
        className="contact-cta"
        href={`/providers/${providerSlug}/claim`}
      >
        Подтвердить владение
      </Link>
    </div>
  );
}
