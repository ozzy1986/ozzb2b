import type { LeadStatus, OutreachStatus } from './types';

export const LEAD_STATUS_LABEL: Record<LeadStatus, string> = {
  new: 'Новая',
  in_progress: 'В работе',
  closed: 'Закрыта',
  spam: 'Спам',
};

export const OUTREACH_STATUS_LABEL: Record<OutreachStatus, string> = {
  draft: 'Черновик',
  sent: 'Отправлено',
  skipped: 'Пропущено',
  failed: 'Ошибка отправки',
};
