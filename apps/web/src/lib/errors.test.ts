import { describe, expect, it } from 'vitest';
import { ApiError } from './api';
import { humanizeError, isApiErrorStatus } from './errors';

describe('humanizeError', () => {
  it('maps known English API details to Russian', () => {
    expect(
      humanizeError(new ApiError(401, 'invalid email or password'), 'auth-login'),
    ).toBe('Неверный адрес электронной почты или пароль.');

    expect(
      humanizeError(new ApiError(409, 'email already registered'), 'auth-register'),
    ).toBe('Пользователь с такой электронной почтой уже зарегистрирован.');

    expect(
      humanizeError(new ApiError(404, 'provider not found'), 'generic'),
    ).toBe('Компания не найдена.');

    expect(
      humanizeError(new ApiError(403, 'admin only'), 'admin-fetch'),
    ).toBe('Действие доступно только администраторам.');

    expect(
      humanizeError(
        new ApiError(400, 'verification meta tag missing or invalid'),
        'claim-verify',
      ),
    ).toContain('Meta-тег');
  });

  it('falls back to status-based messages when detail is unknown', () => {
    expect(humanizeError(new ApiError(429, 'rate_limited'), 'auth-login')).toBe(
      'Слишком много попыток. Подождите немного и повторите.',
    );
    expect(humanizeError(new ApiError(500, 'x'), 'generic')).toBe(
      'Сервер временно недоступен. Попробуйте ещё раз позже.',
    );
  });

  it('adds password/email hints for 422 during registration', () => {
    expect(
      humanizeError(
        new ApiError(422, 'body.password: String should have at least 10'),
        'auth-register',
      ),
    ).toBe('Пароль должен быть не короче 10 символов.');

    expect(
      humanizeError(
        new ApiError(422, 'body.email: value is not a valid email address'),
        'auth-register',
      ),
    ).toBe('Проверьте корректность адреса электронной почты.');
  });

  it('translates network errors without leaking English', () => {
    const err = new TypeError('Failed to fetch');
    const msg = humanizeError(err, 'chat-load');
    expect(msg.toLowerCase()).not.toContain('fetch');
    expect(msg).toBe(
      'Нет связи с сервером. Проверьте интернет и попробуйте ещё раз.',
    );
  });

  it('returns a context-aware fallback for arbitrary errors', () => {
    expect(humanizeError(new Error('boom'), 'auth-login')).toBe(
      'Не удалось войти. Попробуйте ещё раз.',
    );
    expect(humanizeError(null, 'chat-send')).toBe(
      'Не удалось отправить сообщение. Попробуйте ещё раз.',
    );
  });

  it('parses pydantic-style "loc: msg" detail strings', () => {
    // Right-hand side matches a known key.
    expect(
      humanizeError(
        new ApiError(403, 'body: not an owner of this provider'),
        'provider-update',
      ),
    ).toBe('Вы не являетесь владельцем этой компании.');
  });
});

describe('isApiErrorStatus', () => {
  it('matches ApiError with the given status', () => {
    expect(isApiErrorStatus(new ApiError(401, 'x'), 401)).toBe(true);
    expect(isApiErrorStatus(new ApiError(500, 'x'), 401)).toBe(false);
    expect(isApiErrorStatus(new Error('x'), 401)).toBe(false);
  });
});
