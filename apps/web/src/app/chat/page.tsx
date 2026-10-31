import { Suspense } from "react";

import { ChatView } from "@/components/ChatView";

export default function ChatPage() {
  return (
    <Suspense fallback={<p className="p-8 text-muted">Loading the mentor…</p>}>
      <ChatView />
    </Suspense>
  );
}
