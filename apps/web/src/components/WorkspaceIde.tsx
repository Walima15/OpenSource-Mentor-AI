"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { Markdown } from "@/components/Markdown";
import {
  api,
  ChatMessage,
  PendingEdit,
  SearchHit,
  TreeEntry,
  WorkspaceFile,
  WorkspaceInfo,
} from "@/lib/api";

const Editor = dynamic(() => import("@monaco-editor/react"), {
  ssr: false,
  loading: () => <p className="p-4 text-sm text-muted">Loading editor…</p>,
});

function languageFor(path: string): string {
  const ext = path.split(".").pop()?.toLowerCase();
  const known: Record<string, string> = {
    rs: "rust",
    md: "markdown",
    toml: "toml",
    json: "json",
    py: "python",
    js: "javascript",
    ts: "typescript",
    tsx: "typescript",
    yml: "yaml",
    yaml: "yaml",
    sh: "shell",
    c: "c",
    h: "c",
    cpp: "cpp",
  };
  return known[ext || ""] || "plaintext";
}

export function WorkspaceIde({ workspaceId }: { workspaceId: string }) {
  const [info, setInfo] = useState<WorkspaceInfo | null>(null);
  const [entries, setEntries] = useState<TreeEntry[]>([]);
  const [filter, setFilter] = useState("");
  const [hits, setHits] = useState<SearchHit[] | null>(null);
  const [path, setPath] = useState<string | null>(null);
  const [file, setFile] = useState<WorkspaceFile | null>(null);
  const [draft, setDraft] = useState("");
  const [edits, setEdits] = useState<PendingEdit[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [chat, setChat] = useState("");
  const [mode, setMode] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api<WorkspaceInfo>(`api/v1/workspaces/${workspaceId}`)
      .then((body) => {
        if (!cancelled) setInfo(body);
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Workspace not found"));
    api<{ entries: TreeEntry[] }>(`api/v1/workspaces/${workspaceId}/tree`)
      .then((body) => {
        if (!cancelled) setEntries(body.entries);
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Could not read the tree"));
    api<{ edits: PendingEdit[] }>(`api/v1/workspaces/${workspaceId}/edits`)
      .then((body) => {
        if (!cancelled) setEdits(body.edits);
      })
      .catch(() => {
        if (!cancelled) setEdits([]);
      });
    return () => {
      cancelled = true;
    };
  }, [workspaceId]);

  useEffect(() => {
    if (!path) return;
    let cancelled = false;
    api<WorkspaceFile>(`api/v1/workspaces/${workspaceId}/file?path=${encodeURIComponent(path)}`)
      .then((body) => {
        if (cancelled) return;
        setFile(body);
        setDraft(body.text);
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Could not open the file"));
    return () => {
      cancelled = true;
    };
  }, [path, workspaceId]);

  async function refreshEdits() {
    const body = await api<{ edits: PendingEdit[] }>(`api/v1/workspaces/${workspaceId}/edits`);
    setEdits(body.edits);
  }

  const visible = useMemo(() => {
    const needle = filter.trim().toLowerCase();
    return entries.filter((entry) => entry.type === "file" && (!needle || entry.path.toLowerCase().includes(needle)));
  }, [entries, filter]);

  const pending = edits.filter((edit) => edit.path === path);

  async function save() {
    if (!path || !file || file.binary || file.truncated) return;
    setBusy(true);
    setError(null);
    try {
      await api(`api/v1/workspaces/${workspaceId}/file`, {
        method: "POST",
        body: JSON.stringify({ path, text: draft }),
      });
      setFile({ ...file, text: draft, truncated: false, binary: false });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Could not save");
    } finally {
      setBusy(false);
    }
  }

  async function search(event: FormEvent) {
    event.preventDefault();
    const query = filter.trim();
    if (query.length < 2) return;
    setError(null);
    try {
      const body = await api<{ matches: SearchHit[] }>(`api/v1/workspaces/${workspaceId}/search`, {
        method: "POST",
        body: JSON.stringify({ query }),
      });
      setHits(body.matches);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Search failed");
    }
  }

  async function send(text: string) {
    const message = text.trim();
    if (!message || busy) return;
    setBusy(true);
    setError(null);
    setChat("");
    const optimistic: ChatMessage = {
      id: `local-${messages.length}`,
      role: "user",
      content: message,
      tool_trace: [],
      created_at: "",
    };
    setMessages((current) => [...current, optimistic]);
    try {
      const body = await api<{ conversation_id: string; mode: string; message: ChatMessage }>("api/v1/chat", {
        method: "POST",
        body: JSON.stringify({
          message,
          conversation_id: conversationId,
          workspace_id: workspaceId,
          open_path: path,
        }),
      });
      setConversationId(body.conversation_id);
      setMode(body.mode);
      setMessages((current) => [...current.filter((item) => item.id !== optimistic.id), optimistic, body.message]);
      await refreshEdits();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "The mentor could not answer");
    } finally {
      setBusy(false);
    }
  }

  async function decide(editId: string, action: "accept" | "reject") {
    setBusy(true);
    setError(null);
    try {
      await api(`api/v1/workspaces/${workspaceId}/edits/${editId}/${action}`, { method: "POST" });
      await refreshEdits();
      if (path) {
        const body = await api<WorkspaceFile>(
          `api/v1/workspaces/${workspaceId}/file?path=${encodeURIComponent(path)}`,
        );
        setFile(body);
        setDraft(body.text);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Could not update the edit");
    } finally {
      setBusy(false);
    }
  }

  const dirty = file && !file.binary && !file.truncated && draft !== file.text;

  return (
    <div className="grid h-[calc(100vh-4.25rem)] grid-cols-1 lg:grid-cols-[16rem_minmax(0,1fr)_22rem]">
      <aside className="overflow-y-auto border-b border-line lg:border-b-0 lg:border-r">
        <div className="sticky top-0 border-b border-line bg-paper/95 px-3 py-3">
          <Link href="/workspace" className="text-xs uppercase tracking-wide text-muted hover:text-rust">
            Workspaces
          </Link>
          <h1 className="mt-1 font-serif text-2xl">{info?.name || "Workspace"}</h1>
          <p className="text-xs text-muted">
            {info ? `${info.owner}/${info.repo}` : ""}
          </p>
          <form onSubmit={search} className="mt-3">
            <label className="sr-only" htmlFor="workspace-filter">
              Filter or search
            </label>
            <input
              id="workspace-filter"
              value={filter}
              onChange={(event) => setFilter(event.target.value)}
              placeholder="Filter files, Enter to search"
              className="w-full rounded-lg border border-line bg-card px-2 py-1.5 text-sm outline-none focus:border-rust"
            />
          </form>
        </div>
        <ul className="px-2 py-2 text-sm">
          {visible.slice(0, 400).map((entry) => (
            <li key={entry.path}>
              <button
                type="button"
                onClick={() => setPath(entry.path)}
                className={`block w-full truncate rounded px-2 py-1 text-left ${
                  path === entry.path ? "bg-card text-ink" : "text-muted hover:bg-card hover:text-ink"
                }`}
                title={entry.path}
              >
                {entry.path}
              </button>
            </li>
          ))}
        </ul>
        {hits ? (
          <div className="border-t border-line px-3 py-3">
            <p className="text-xs uppercase tracking-wide text-muted">{hits.length} content matches</p>
            <ul className="mt-2 space-y-1 text-xs">
              {hits.map((hit) => (
                <li key={`${hit.path}:${hit.line}:${hit.text}`}>
                  <button type="button" className="text-left hover:text-rust" onClick={() => setPath(hit.path)}>
                    <span className="text-ink">
                      {hit.path}:{hit.line}
                    </span>{" "}
                    <span className="text-muted">{hit.text}</span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </aside>
      <section className="flex min-h-0 min-w-0 flex-col border-b border-line lg:border-b-0 lg:border-r">
        <div className="flex items-center justify-between gap-3 border-b border-line px-3 py-2">
          <p className="truncate text-sm">{path || "Choose a file"}</p>
          <button
            type="button"
            disabled={!dirty || busy}
            onClick={() => void save()}
            className="rounded-full bg-ink px-3 py-1 text-xs text-paper disabled:opacity-40"
          >
            Save
          </button>
        </div>
        {pending.map((edit) => (
          <div key={edit.id} className="border-b border-line bg-card px-3 py-3">
            <p className="text-sm">Proposed diff. It is not in the file until you accept it.</p>
            <pre className="mt-2 max-h-48 overflow-auto rounded-lg bg-ink p-3 text-xs text-paper">{edit.diff}</pre>
            <div className="mt-2 flex gap-2">
              <button
                type="button"
                disabled={busy}
                onClick={() => void decide(edit.id, "accept")}
                className="rounded-full bg-moss px-3 py-1 text-xs text-paper"
              >
                Accept
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={() => void decide(edit.id, "reject")}
                className="rounded-full border border-line px-3 py-1 text-xs"
              >
                Reject
              </button>
            </div>
          </div>
        ))}
        <div className="min-h-[20rem] flex-1">
          {file?.binary ? (
            <p className="p-4 text-sm text-muted">This file is binary. The IDE will not open it.</p>
          ) : file?.truncated ? (
            <p className="p-4 text-sm text-muted">This file is too large to edit here. Open it in your own editor.</p>
          ) : path ? (
            <Editor
              height="100%"
              language={languageFor(path)}
              theme="vs"
              value={draft}
              onChange={(value) => setDraft(value ?? "")}
              options={{
                minimap: { enabled: false },
                fontSize: 13,
                wordWrap: "on",
                scrollBeyondLastLine: false,
                padding: { top: 12 },
              }}
            />
          ) : (
            <p className="p-4 text-sm text-muted">Open a file from the tree. The project’s rules are on the right.</p>
          )}
        </div>
      </section>
      <aside className="flex min-h-0 flex-col">
        <div className="max-h-[40%] space-y-3 overflow-y-auto border-b border-line px-3 py-3 text-sm">
          <p className="text-xs text-muted">
            No terminal. Tests stay listed here so you can run them yourself.             Suggested model: <code className="whitespace-nowrap">{info?.recommended_model}</code>
          </p>
          <RuleList title="Contributing" items={info?.contributing || []} />
          <RuleList title="Review and test checklist" items={info?.checklist || []} />
          <RuleList title="Test commands" items={info?.test_steps || []} code />
        </div>
        <div className="flex min-h-0 flex-1 flex-col">
          <div className="min-h-0 flex-1 space-y-3 overflow-y-auto px-3 py-3">
            {messages.length === 0 ? (
              <div>
                <h2 className="font-serif text-xl">Ask about this repo</h2>
                <button
                  type="button"
                  disabled={!path}
                  onClick={() => void send("Explain this file")}
                  className="mt-3 rounded-full border border-line bg-card px-3 py-1.5 text-sm disabled:opacity-40"
                >
                  Explain this file
                </button>
              </div>
            ) : null}
            {messages.map((message) => (
              <article
                key={message.id}
                className={`rounded-xl px-3 py-2 text-sm ${
                  message.role === "user" ? "bg-[#f6e2d4]" : "border border-line bg-card"
                }`}
              >
                <p className="mb-1 text-xs uppercase tracking-wide text-muted">
                  {message.role === "user" ? "You" : "OSMA"}
                </p>
                {message.role === "assistant" ? <Markdown text={message.content} /> : <p>{message.content}</p>}
              </article>
            ))}
            {mode === "guide" ? (
              <p className="text-xs text-muted">Guide mode is on. No model was called.</p>
            ) : null}
            {error ? <p className="text-sm text-rust">{error}</p> : null}
          </div>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              void send(chat);
            }}
            className="border-t border-line p-3"
          >
            <label className="sr-only" htmlFor="workspace-chat">
              Message
            </label>
            <textarea
              id="workspace-chat"
              value={chat}
              onChange={(event) => setChat(event.target.value)}
              rows={2}
              maxLength={8000}
              placeholder="Ask about the open file or a contribution"
              className="w-full resize-none rounded-xl border border-line bg-card px-3 py-2 text-sm outline-none focus:border-rust"
            />
            <button
              type="submit"
              disabled={busy || !chat.trim()}
              className="mt-2 rounded-full bg-rust px-4 py-1.5 text-sm text-paper disabled:opacity-50"
            >
              Send
            </button>
          </form>
        </div>
      </aside>
    </div>
  );
}

function RuleList({ title, items, code = false }: { title: string; items: string[]; code?: boolean }) {
  if (!items.length) return null;
  return (
    <section>
      <h2 className="font-serif text-lg">{title}</h2>
      <ul className="mt-1 space-y-1 text-xs leading-5 text-muted">
        {items.map((item) => (
          <li key={item}>{code ? <code>{item}</code> : item}</li>
        ))}
      </ul>
    </section>
  );
}
