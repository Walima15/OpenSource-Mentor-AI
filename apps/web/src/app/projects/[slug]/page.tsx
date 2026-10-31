import { ProjectView } from "@/components/ProjectView";

export default async function ProjectPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  return <ProjectView slug={slug} />;
}
