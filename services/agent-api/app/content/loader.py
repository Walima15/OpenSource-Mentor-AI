"""Load and validate the curated curriculum and project catalog."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.content.contribute import LESSONS as CONTRIBUTE_LESSONS
from app.content.fundamentals import LESSONS as FUNDAMENTAL_LESSONS
from app.content.lightning import LESSONS as LIGHTNING_LESSONS
from app.content.projects import PROJECTS as PROJECT_DICTS


class Source(BaseModel):
    title: str
    url: str

    @field_validator("url")
    @classmethod
    def _https(cls, value: str) -> str:
        if not value.startswith("https://"):
            raise ValueError("curriculum links must be https")
        return value


class QuizQuestion(BaseModel):
    prompt: str
    choices: list[str] = Field(min_length=2, max_length=6)
    answer: int
    explanation: str

    @field_validator("answer")
    @classmethod
    def _in_range(cls, value: int, info) -> int:
        choices = info.data.get("choices") or []
        if choices and not 0 <= value < len(choices):
            raise ValueError("quiz answer is out of range")
        return value


class Lesson(BaseModel):
    id: str
    path_id: str
    title: str
    order: int
    summary: str
    concepts: list[str]
    keywords: list[str]
    sources: list[Source]
    body: str
    quiz: list[QuizQuestion] = Field(min_length=1)


class LearningPath(BaseModel):
    id: str
    title: str
    summary: str
    audience: str
    order: int


class DocLink(BaseModel):
    title: str
    url: str

    @field_validator("url")
    @classmethod
    def _https_or_known_http_doc(cls, value: str) -> str:
        # The Miniscript reference site is served over http. Everything else is https.
        if value.startswith("https://"):
            return value
        if value == "http://bitcoin.sipa.be/miniscript/":
            return value
        raise ValueError("unexpected project doc URL")


class CodePointer(BaseModel):
    path: str
    why: str


class Project(BaseModel):
    slug: str
    name: str
    owner: str
    repo: str
    language: str
    difficulty: str
    summary: str
    tags: list[str]
    aliases: list[str]
    issue_labels: list[str] = Field(min_length=1)
    docs: list[DocLink]
    prerequisites: list[str]
    setup_steps: list[str]
    test_steps: list[str]
    contributing: list[str]
    code_map: list[CodePointer]
    review_notes: list[str]


PATHS: tuple[LearningPath, ...] = (
    LearningPath(
        id="bitcoin-fundamentals",
        title="Bitcoin fundamentals",
        summary="UTXOs, transactions, scripts, blocks, consensus, the peer-to-peer network, the mempool, and BIPs.",
        audience="Developers who can program and have not yet worked inside a Bitcoin codebase.",
        order=1,
    ),
    LearningPath(
        id="lightning",
        title="Lightning",
        summary="Channels, HTLCs, routing, and how LDK, LND, Core Lightning, and the BOLTs fit together.",
        audience="Contributors heading toward Lightning implementations or the specification.",
        order=2,
    ),
    LearningPath(
        id="contribution-craft",
        title="Contribution craft",
        summary="Project maps, reading code, ACK and NACK, tests, signed commits, pull requests, and where to talk.",
        audience="Anyone about to open or review a pull request on a Bitcoin project.",
        order=3,
    ),
)


def _load_lessons() -> dict[str, Lesson]:
    lessons = [Lesson.model_validate(item) for item in (
        *FUNDAMENTAL_LESSONS,
        *LIGHTNING_LESSONS,
        *CONTRIBUTE_LESSONS,
    )]
    by_id: dict[str, Lesson] = {}
    for lesson in lessons:
        if lesson.id in by_id:
            raise RuntimeError(f"duplicate lesson id {lesson.id}")
        by_id[lesson.id] = lesson
    path_ids = {path.id for path in PATHS}
    for lesson in lessons:
        if lesson.path_id not in path_ids:
            raise RuntimeError(f"lesson {lesson.id} has unknown path {lesson.path_id}")
    return by_id


def _load_projects() -> dict[str, Project]:
    projects = [Project.model_validate(item) for item in PROJECT_DICTS]
    by_slug: dict[str, Project] = {}
    for project in projects:
        if project.slug in by_slug:
            raise RuntimeError(f"duplicate project {project.slug}")
        by_slug[project.slug] = project
    return by_slug


LESSONS: dict[str, Lesson] = _load_lessons()
PROJECTS: dict[str, Project] = _load_projects()


def lessons_for_path(path_id: str) -> list[Lesson]:
    return sorted(
        (lesson for lesson in LESSONS.values() if lesson.path_id == path_id),
        key=lambda lesson: lesson.order,
    )


def public_quiz(lesson: Lesson) -> list[dict]:
    return [{"prompt": item.prompt, "choices": item.choices} for item in lesson.quiz]


def public_lesson(lesson: Lesson) -> dict:
    payload = lesson.model_dump()
    payload["quiz"] = public_quiz(lesson)
    return payload
