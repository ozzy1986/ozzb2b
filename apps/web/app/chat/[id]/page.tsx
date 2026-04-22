import type { Metadata } from 'next';
import { ChatPageClient } from '@/components/chat/ChatPageClient';

export const metadata: Metadata = {
  title: 'Беседа',
  description: 'Чат с компанией.',
};

type RouteParams = Promise<{ id: string }>;

export default async function ChatPage({ params }: { params: RouteParams }) {
  const { id } = await params;
  return <ChatPageClient conversationId={id} />;
}
