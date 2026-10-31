import assert from "node:assert/strict";
import { test } from "node:test";
import { safeRedirectPath, sameOriginRedirect } from "./safe-redirect.ts";

test("allows a same-site path", () => {
  assert.equal(safeRedirectPath("/dashboard"), "/dashboard");
  assert.equal(
    safeRedirectPath("/dashboard/repos/abc"),
    "/dashboard/repos/abc",
  );
});

test("rejects open-redirect shapes", () => {
  assert.equal(safeRedirectPath("@evil.example"), "/dashboard");
  assert.equal(safeRedirectPath("//evil.example"), "/dashboard");
  assert.equal(safeRedirectPath("/\\evil.example"), "/dashboard");
  assert.equal(safeRedirectPath("https://evil.example"), "/dashboard");
  assert.equal(safeRedirectPath("/foo//bar"), "/dashboard");
  assert.equal(safeRedirectPath(null), "/dashboard");
  assert.equal(safeRedirectPath("  "), "/dashboard");
});

test("sameOriginRedirect keeps the configured origin", () => {
  assert.equal(
    sameOriginRedirect("https://osma.example", "/dashboard/sessions"),
    "https://osma.example/dashboard/sessions",
  );
  assert.equal(
    sameOriginRedirect("https://osma.example", "@evil.example"),
    "https://osma.example/dashboard",
  );
});
