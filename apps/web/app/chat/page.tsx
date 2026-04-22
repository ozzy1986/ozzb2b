import type { Metadata } from 'next';
import { ChatInbox } from '@/components/chat/ChatInbox';

export const metadata: Metadata = {
  title: 'Чаты',
  description: 'Ваши беседы с B2B-подрядчиками.',
};

export default function ChatIndexPage() {
  return (
    <div>
      <div className="hero">
        <h1>Чаты</h1>
        <p>Общайтесь с компаниями, которые вас заинтересовали.</p>
      </div>
      <ChatInbox activeConversationId={null} />
    </div>
  );
}
