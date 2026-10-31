"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useEffect, useRef, useState } from "react";

import { api, ChatMessage, Conversation } from "@/lib/api";
import { Markdown } from "@/components/Markdown";

const STARTERS = [
  "Explain UTXOs",
  "How do ACK and NACK work in Bitcoin Core?",
  "How do I build Bitcoin Core?",
  "Find good first issues in rust-bitcoin",
  "Plan a contribution to BDK",
];

export function ChatView({ conversationId }: { conversationId?: string }) {
  const router = useRouter();
  const params = useSearchParams();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const preset = params.get("q") ?? "";
  const [draft, setDraft] = useState(() => preset.slice(0, 8000));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<string | null>(null);
  const scroller = useRef<HTMLDivElement>(null);
  const localIds = useRef(0);

  useEffect(() => {
    api<{ conversations: Conversation[] }>("api/v1/conversations")
      .then((body) => setConversations(body.conversations))
      .catch(() => setConversations([]));
  }, [conversationId, messages.length]);

  useEffect(() => {
    if (!conversationId) return;
    let cancelled = false;
    api<{ messages: ChatMessage[] }>(`api/v1/conversations/${conversationId}`)
      .then((body) => {
        if (!cancelled) setMessages(body.messages);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Could not load the session");
      });
    return () => {
      cancelled = true;
    };
  }, [conversationId]);

  useEffect(() => {
    scroller.current?.scrollTo({ top: scroller.current.scrollHeight });
  }, [messages, busy]);

  async function submit(text: string) {
    const message = text.trim();
    if (!message || busy) return;
    setBusy(true);
    setError(null);
    setDraft("");
    localIds.current += 1;
    const optimistic: ChatMessage = {
      id: `local-${localIds.current}`,
      role: "user",
      content: message,
      tool_trace: [],
      created_at: "",
    };
    setMessages((current) => [...current, optimistic]);
    try {
      const body = await api<{
        conversation_id: string;
        mode: string;
        message: ChatMessage;
      }>("api/v1/chat", {
        method: "POST",
        body: JSON.stringify({
          message,
          conversation_id: conversationId,
        }),
      });
      setMode(body.mode);
      if (!conversationId) {
        router.replace(`/chat/${body.conversation_id}`);
        return;
      }
      setMessages((current) => [...current.filter((item) => item.id !== optimistic.id), optimistic, body.message]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "The mentor could not answer");
    } finally {
      setBusy(false);
    }
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void submit(draft);
  }

  async function removeConversation(id: string) {
    await api(`api/v1/conversations/${id}`, { method: "DELETE" });
    if (id === conversationId) router.push("/chat");
    setConversations((current) => current.filter((item) => item.id !== id));
  }

  return (
    <div className="mx-auto grid h-[calc(100vh-4.25rem)] max-w-6xl grid-cols-1 md:grid-cols-[16rem_1fr]">
      <aside className="hidden overflow-y-auto border-r border-line px-3 py-4 md:block">
        <Link href="/chat" className="block rounded-full bg-ink px-3 py-2 text-center text-sm text-paper">
          New session
        </Link>
        <ul className="mt-4 space-y-1">
          {conversations.map((conversation) => (
            <li key={conversation.id} className="group flex items-start gap-1">
              <Link
                href={`/chat/${conversation.id}`}
                className={`block flex-1 rounded-lg px-2 py-1.5 text-sm ${
                  conversation.id === conversationId ? "bg-card text-ink" : "text-muted hover:bg-card"
                }`}
              >
                {conversation.title}
              </Link>
              <button
                type="button"
                className="px-1 text-xs text-muted opacity-0 hover:text-rust group-hover:opacity-100"
                onClick={() => void removeConversation(conversation.id)}
                aria-label={`Delete ${conversation.title}`}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      </aside>
      <section className="flex min-h-0 flex-col">
        <div ref={scroller} className="min-h-0 flex-1 space-y-4 overflow-y-auto px-4 py-6">
          {messages.length === 0 ? (
            <div className="mx-auto max-w-2xl pt-8">
              <h1 className="font-serif text-4xl tracking-tight">What do you want to learn?</h1>
              <p className="mt-3 max-w-xl text-muted">
                Ask about the protocol, a project setup, a first issue, or a pull request. OSMA will teach the
                step and point at the repository. It will not ACK code for you.
              </p>
              <div className="mt-6 flex flex-wrap gap-2">
                {STARTERS.map((starter) => (
                  <button
                    key={starter}
                    type="button"
                    className="rounded-full border border-line bg-card px-3 py-1.5 text-left text-sm hover:border-rust"
                    onClick={() => void submit(starter)}
                  >
                    {starter}
                  </button>
                ))}
              </div>
            </div>
          ) : null}
          {messages.map((message) => (
            <article
              key={message.id}
              className={`mx-auto max-w-2xl rounded-2xl px-4 py-3 ${
                message.role === "user" ? "bg-[#f6e2d4]" : "border border-line bg-card shadow-card"
              }`}
            >
              <p className="mb-1 text-xs uppercase tracking-wide text-muted">
                {message.role === "user" ? "You" : "OSMA"}
              </p>
              {message.role === "assistant" ? <Markdown text={message.content} /> : <p className="whitespace-pre-wrap">{message.content}</p>}
              {message.tool_trace?.length ? (
                <ul className="mt-3 flex flex-wrap gap-1.5">
                  {message.tool_trace.map((trace, index) => (
                    <li
                      key={`${trace.name}-${index}`}
                      className="rounded-full bg-paper px-2 py-0.5 text-xs text-muted"
                      title={trace.summary}
                    >
                      {trace.ok ? trace.name : `${trace.name} failed`}
                    </li>
                  ))}
                </ul>
              ) : null}
            </article>
          ))}
          {busy ? <p className="mx-auto max-w-2xl text-sm text-muted">Working through the notes…</p> : null}
          {mode === "guide" ? (
            <p className="mx-auto max-w-2xl text-xs text-muted">
              Guide mode is on. Add OPENAI_API_KEY to .env for a conversational mentor. The curriculum and GitHub
              tools still run.
            </p>
          ) : null}
          {error ? <p className="mx-auto max-w-2xl text-sm text-rust">{error}</p> : null}
        </div>
        <form onSubmit={onSubmit} className="border-t border-line bg-paper/90 px-4 py-3">
          <div className="mx-auto flex max-w-2xl gap-2">
            <label className="sr-only" htmlFor="mentor-message">
              Message
            </label>
            <textarea
              id="mentor-message"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  void submit(draft);
                }
              }}
              rows={2}
              maxLength={8000}
              placeholder="Ask about a concept, a repo, or a pull request"
              className="min-h-[3.2rem] flex-1 resize-none rounded-xl border border-line bg-card px-3 py-2 text-sm outline-none focus:border-rust"
            />
            <button
              type="submit"
              disabled={busy || !draft.trim()}
              className="self-end rounded-full bg-rust px-4 py-2 text-sm text-paper disabled:opacity-50"
            >
              Send
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
