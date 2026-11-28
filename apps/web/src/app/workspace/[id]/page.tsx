"use client";

import { useParams } from "next/navigation";

import { WorkspaceIde } from "@/components/WorkspaceIde";

export default function WorkspaceIdePage() {
  const params = useParams<{ id: string }>();
  const workspaceId = Array.isArray(params.id) ? params.id[0] : params.id;
  return <WorkspaceIde workspaceId={workspaceId} />;
}
