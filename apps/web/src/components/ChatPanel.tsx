"use client";

import { useEffect, useRef, useState } from "react";
import { api, streamChat } from "@/lib/api-client";
import { Markdown } from "@/components/Markdown";
import type { MentorMessage } from "@/types";

export function ChatPanel({ sessionId }: { sessionId: string }) {
  const [messages, setMessages] = useState<MentorMessage[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState("");
  const [busy, setBusy] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api
      .getSessionMessages(sessionId)
      .then(setMessages)
      .catch(() => setMessages([]));
  }, [sessionId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streaming]);

  async function send() {
    const text = input.trim();
    if (!text || busy) return;
    setBusy(true);
    setInput("");
    const userMsg: MentorMessage = {
      id: `local-${Date.now()}`,
      session_id: sessionId,
      role: "user",
      content: text,
      metadata: null,
      created_at: new Date().toISOString(),
    };
    setMessages((m) => [...m, userMsg]);
    setStreaming("");

    let acc = "";
    try {
      await streamChat(sessionId, text, (delta) => {
        acc += delta;
        setStreaming(acc);
      });
    } catch {
      acc = acc || "Sorry, something went wrong generating a response.";
    }

    setMessages((m) => [
      ...m,
      {
        id: `local-a-${Date.now()}`,
        session_id: sessionId,
        role: "assistant",
        content: acc,
        metadata: null,
        created_at: new Date().toISOString(),
      },
    ]);
    setStreaming("");
    setBusy(false);
  }

  return (
    <div className="flex h-full flex-col">
      <div className="scrollbar-thin flex-1 space-y-4 overflow-y-auto p-4">
        {messages.length === 0 && !streaming && (
          <p className="text-sm text-slate-500">
            Ask the mentor anything about this repository or issue.
          </p>
        )}
        {messages.map((m) => (
          <Bubble key={m.id} role={m.role}>
            <Markdown content={m.content} />
          </Bubble>
        ))}
        {streaming && (
          <Bubble role="assistant">
            <Markdown content={streaming} />
          </Bubble>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="border-t border-surface-border p-3">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
            rows={2}
            placeholder="Message your mentor..."
            className="input resize-none"
          />
          <button onClick={send} disabled={busy} className="btn-primary">
            {busy ? "..." : "Send"}
          </button>
        </div>
      </div>
    </div>
  );
}

function Bubble({
  role,
  children,
}: {
  role: string;
  children: React.ReactNode;
}) {
  const isUser = role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-xl px-4 py-3 ${
          isUser
            ? "bg-brand-600/20 text-slate-100"
            : "border border-surface-border bg-surface-card"
        }`}
      >
        {children}
      </div>
    </div>
  );
}
