import { notFound } from "next/navigation";
import { Suspense } from "react";

import { ChatView } from "@/components/ChatView";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export default async function ConversationPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  if (!UUID.test(id)) notFound();
  return (
    <Suspense fallback={<p className="p-8 text-muted">Loading the session…</p>}>
      <ChatView conversationId={id} />
    </Suspense>
  );
}
