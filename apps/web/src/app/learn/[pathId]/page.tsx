import { PathView } from "@/components/PathView";

export default async function PathPage({ params }: { params: Promise<{ pathId: string }> }) {
  const { pathId } = await params;
  return <PathView pathId={pathId} />;
}
