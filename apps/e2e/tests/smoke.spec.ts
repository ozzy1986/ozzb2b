import { expect, test } from '@playwright/test';

test.describe('site smoke', () => {
  test('home page renders hero even when API is unavailable', async ({ page }) => {
    const response = await page.goto('/');
    expect(response?.ok()).toBeTruthy();

    await expect(
      page.getByRole('heading', { level: 1, name: /B2B-подрядчика/i }),
    ).toBeVisible();
    await expect(page.getByRole('button', { name: 'Искать' })).toBeVisible();
    // Use exact match: the page also renders a "Все компании →" link which
    // otherwise trips Playwright's strict-mode matcher on "Компании".
    await expect(
      page.getByRole('link', { name: 'Компании', exact: true }),
    ).toBeVisible();
  });

  test('login page shows client-side validation on empty submit', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByRole('heading', { name: 'Вход' })).toBeVisible();

    // The form is intentionally `noValidate` at the React level, but the
    // native HTML `required` / `type=email` attributes still provide a
    // baseline we want to guarantee. Submitting with empty inputs must
    // not navigate and the email field must report invalid.
    const emailInput = page.getByRole('textbox', { name: 'Электронная почта' });
    await expect(emailInput).toBeVisible();

    await page.getByRole('button', { name: /Войти/i }).click();

    const valid = await emailInput.evaluate(
      (el) => (el as HTMLInputElement).checkValidity(),
    );
    expect(valid).toBe(false);
    await expect(page).toHaveURL(/\/login$/);
  });

  test('login page links through to registration', async ({ page }) => {
    await page.goto('/login');
    await page.getByRole('link', { name: /Зарегистрироваться/i }).click();
    await expect(page).toHaveURL(/\/register/);
    await expect(page.getByRole('heading', { name: /Регистрация/i })).toBeVisible();
  });

  test('register page enforces minimum password length', async ({ page }) => {
    await page.goto('/register');

    await page.getByRole('textbox', { name: 'Электронная почта' }).fill('user@example.com');

    // The password input is of type=password and has no accessible text label
    // because the rendered <label> wraps both label and input; target it by
    // type, which keeps the selector stable across copy changes.
    const password = page.locator('input[type="password"]');
    await password.fill('short');

    await page.getByRole('button', { name: /Зарегистрироваться/i }).click();

    const validity = await password.evaluate(
      (el) => (el as HTMLInputElement).checkValidity(),
    );
    expect(validity).toBe(false);
    await expect(page).toHaveURL(/\/register$/);
  });

  test('unknown route serves the built-in 404 page', async ({ page }) => {
    const res = await page.goto('/definitely-not-a-real-route');
    expect(res?.status()).toBe(404);
  });
});
