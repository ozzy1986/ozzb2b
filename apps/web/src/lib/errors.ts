import { ApiError } from './api';

// Translates known API/runtime errors into human-friendly Russian messages.
// The API intentionally returns stable English "detail" strings (used by
// clients and tests). We map them to localized messages on the frontend
// instead of leaking raw backend strings to end users.

const DETAIL_MAP: Record<string, string> = {
  // catalog
  'provider not found': 'Компания не найдена.',
  // admin / roles
  'admin only': 'Действие доступно только администраторам.',
  'not an owner of this provider': 'Вы не являетесь владельцем этой компании.',
  // auth + sessions
  'authentication required': 'Необходима авторизация.',
  'missing refresh token': 'Сессия истекла. Войдите снова.',
  'invalid subject': 'Сессия недействительна. Войдите снова.',
  'user not found': 'Пользователь не найден.',
  'email already registered':
    'Пользователь с такой электронной почтой уже зарегистрирован.',
  'invalid email or password': 'Неверный адрес электронной почты или пароль.',
  'refresh token not found': 'Сессия недействительна. Войдите снова.',
  'refresh token already used': 'Сессия недействительна. Войдите снова.',
  'refresh token expired': 'Сессия истекла. Войдите снова.',
  'refresh token malformed': 'Сессия недействительна. Войдите снова.',
  'unexpected token type': 'Сессия недействительна. Войдите снова.',
  'malformed token payload': 'Сессия недействительна. Войдите снова.',
  // claims
  'claim not found': 'Заявка на подтверждение не найдена.',
  'provider already claimed':
    'Эта компания уже подтверждена другим пользователем.',
  'provider has no website':
    'В карточке компании не указан сайт — подтверждение владения недоступно.',
  'no pending claim for this user and provider':
    'Активная заявка не найдена. Начните подтверждение заново.',
  'claim references missing entities':
    'Заявка ссылается на удалённые данные. Создайте её заново.',
  'verification meta tag missing or invalid':
    'Meta-тег не найден на главной странице сайта или его значение не совпадает. Разместите тег и попробуйте ещё раз.',
  // chat
  'conversation not found': 'Беседа не найдена.',
  'access denied': 'Доступ запрещён.',
  'message body must not be empty': 'Сообщение не может быть пустым.',
};

const STATUS_DEFAULT: Record<number, string> = {
  400: 'Некорректные данные. Проверьте поля формы.',
  401: 'Необходима авторизация.',
  403: 'Действие запрещено.',
  404: 'Данные не найдены.',
  409: 'Конфликт данных. Обновите страницу и попробуйте ещё раз.',
  422: 'Проверьте корректность введённых данных.',
  429: 'Слишком много попыток. Подождите немного и повторите.',
  500: 'Сервер временно недоступен. Попробуйте ещё раз позже.',
  502: 'Сервер временно недоступен. Попробуйте ещё раз позже.',
  503: 'Сервер временно недоступен. Попробуйте ещё раз позже.',
  504: 'Сервер не отвечает. Попробуйте ещё раз позже.',
};

const NETWORK_HINTS = [
  'failed to fetch',
  'networkerror',
  'network request failed',
  'load failed',
  'fetch failed',
];

const TIMEOUT_HINTS = ['timeout', 'timed out'];

export type ErrorContext =
  | 'generic'
  | 'auth-login'
  | 'auth-register'
  | 'auth-logout'
  | 'claim-init'
  | 'claim-verify'
  | 'chat-open'
  | 'chat-load'
  | 'chat-send'
  | 'chat-socket'
  | 'provider-update'
  | 'admin-fetch';

const CONTEXT_FALLBACK: Record<ErrorContext, string> = {
  generic: 'Что-то пошло не так. Попробуйте ещё раз.',
  'auth-login': 'Не удалось войти. Попробуйте ещё раз.',
  'auth-register': 'Не удалось создать аккаунт. Попробуйте ещё раз.',
  'auth-logout': 'Не удалось выйти из аккаунта.',
  'claim-init': 'Не удалось начать подтверждение. Попробуйте ещё раз.',
  'claim-verify':
    'Не удалось проверить meta-тег. Проверьте размещение и попробуйте ещё раз.',
  'chat-open': 'Не удалось открыть чат. Попробуйте ещё раз.',
  'chat-load': 'Не удалось загрузить беседу. Обновите страницу.',
  'chat-send': 'Не удалось отправить сообщение. Попробуйте ещё раз.',
  'chat-socket': 'Потеряно соединение с чатом. Переподключаемся…',
  'provider-update': 'Не удалось сохранить изменения. Попробуйте ещё раз.',
  'admin-fetch': 'Не удалось загрузить данные. Попробуйте ещё раз.',
};

function matchKnownDetail(detail: string): string | null {
  const norm = detail.trim().toLowerCase();
  if (DETAIL_MAP[norm]) return DETAIL_MAP[norm];
  // Pydantic validation errors are serialized as "body.email: field required";
  // try the right-hand side as a fallback before giving up.
  const colon = detail.indexOf(':');
  if (colon > 0) {
    const rhs = detail.slice(colon + 1).trim().toLowerCase();
    if (DETAIL_MAP[rhs]) return DETAIL_MAP[rhs];
  }
  return null;
}

function isNetworkError(err: Error): boolean {
  const msg = (err.message ?? '').toLowerCase();
  const name = (err.name ?? '').toLowerCase();
  if (name === 'typeerror' && msg.includes('fetch')) return true;
  return NETWORK_HINTS.some((n) => msg.includes(n));
}

function isTimeoutError(err: Error): boolean {
  const msg = (err.message ?? '').toLowerCase();
  const name = (err.name ?? '').toLowerCase();
  if (name === 'aborterror' || name === 'timeouterror') return true;
  return TIMEOUT_HINTS.some((t) => msg.includes(t));
}

/** Converts unknown runtime errors to a user-facing Russian message. */
export function humanizeError(
  err: unknown,
  context: ErrorContext = 'generic',
): string {
  if (err instanceof ApiError) {
    // Context-specific 422 hints that are nicer than the generic fallback.
    if (err.status === 422 && context === 'auth-register') {
      const d = err.detail.toLowerCase();
      if (d.includes('password')) {
        return 'Пароль должен быть не короче 10 символов.';
      }
      if (d.includes('email')) {
        return 'Проверьте корректность адреса электронной почты.';
      }
    }
    if (err.detail) {
      const mapped = matchKnownDetail(err.detail);
      if (mapped) return mapped;
    }
    const byStatus = STATUS_DEFAULT[err.status];
    if (byStatus) return byStatus;
    return CONTEXT_FALLBACK[context];
  }
  if (err instanceof Error) {
    if (isNetworkError(err)) {
      return 'Нет связи с сервером. Проверьте интернет и попробуйте ещё раз.';
    }
    if (isTimeoutError(err)) {
      return 'Сервер не отвечает. Попробуйте ещё раз.';
    }
  }
  return CONTEXT_FALLBACK[context];
}

/** True for ApiError with the given HTTP status. Useful for redirect flows. */
export function isApiErrorStatus(err: unknown, status: number): boolean {
  return err instanceof ApiError && err.status === status;
}
