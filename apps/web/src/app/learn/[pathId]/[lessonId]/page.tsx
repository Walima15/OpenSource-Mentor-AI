import { LessonView } from "@/components/LessonView";

export default async function LessonPage({
  params,
}: {
  params: Promise<{ pathId: string; lessonId: string }>;
}) {
  const { pathId, lessonId } = await params;
  return <LessonView pathId={pathId} lessonId={lessonId} />;
}
