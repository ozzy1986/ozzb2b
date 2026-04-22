#!/usr/bin/env bash
# Phase 6 smoke: admin page reachable, breadcrumbs + JSON-LD on provider
# pages, "Сбросить" on the listing, and security headers still present.
set -u

echo "--- /admin/analytics reachable (SSR) ---"
curl -sS -o /tmp/admin.html -w 'status=%{http_code}\n' https://ozzb2b.com/admin/analytics
grep -oE 'Аналитика|Требуется вход|Доступ закрыт' /tmp/admin.html | sort -u | head -3

echo
echo "--- /providers/agima has BreadcrumbList + Organization JSON-LD ---"
curl -sS https://ozzb2b.com/providers/agima -o /tmp/detail.html
grep -oE '"@type":"(BreadcrumbList|Organization|ListItem)"' /tmp/detail.html | sort -u

echo
echo "--- /providers/agima shows breadcrumb trail labels ---"
grep -oE 'Главная|Компании|AGIMA' /tmp/detail.html | sort -u

echo
echo "--- /providers listing: clear-filters link when filter is active ---"
curl -sS "https://ozzb2b.com/providers?country=RU&category=it" -o /tmp/list.html
grep -oE 'filter-clear|Сбросить' /tmp/list.html | sort -u

echo
echo "--- SiteNav admin entry hidden for anonymous ---"
curl -sS https://ozzb2b.com/ -o /tmp/home.html
grep -c '/admin/analytics' /tmp/home.html

echo
echo "--- security headers still present ---"
curl -sSI https://ozzb2b.com/ | grep -iE '^(strict-transport|x-content-type|x-frame|referrer|permissions)'
