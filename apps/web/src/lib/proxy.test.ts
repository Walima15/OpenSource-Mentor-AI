import assert from "node:assert/strict";
import test from "node:test";

import { agentBaseUrl, safeAgentPath } from "./proxy.ts";

test("allows mentor API paths", () => {
  assert.equal(safeAgentPath(["health"]), "health");
  assert.equal(safeAgentPath(["api", "v1", "chat"]), "api/v1/chat");
  assert.equal(
    safeAgentPath(["api", "v1", "curriculum", "lessons", "utxos"]),
    "api/v1/curriculum/lessons/utxos",
  );
  assert.equal(
    safeAgentPath(["api", "v1", "workspaces", "projects"]),
    "api/v1/workspaces/projects",
  );
});

test("rejects traversal and off-site paths", () => {
  assert.throws(() => safeAgentPath(["..", "etc", "passwd"]));
  assert.throws(() => safeAgentPath(["api", "v1", "..", "health"]));
  assert.throws(() => safeAgentPath(["https://example.com"]));
  assert.throws(() => safeAgentPath(["api", "v1", "chat?x=1"]));
});

test("agent base url is limited to the local API", () => {
  assert.equal(agentBaseUrl("http://127.0.0.1:8000"), "http://127.0.0.1:8000");
  assert.equal(agentBaseUrl("http://agent-api:8000/ignored"), "http://agent-api:8000");
  assert.throws(() => agentBaseUrl("http://169.254.169.254/"));
  assert.throws(() => agentBaseUrl("https://user:secret@127.0.0.1:8000"));
  assert.throws(() => agentBaseUrl("file:///tmp/osma"));
});
