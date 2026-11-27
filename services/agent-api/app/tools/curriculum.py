"""Curriculum tools: lessons, concepts, and quizzes."""

from __future__ import annotations

import re

from app.content.loader import LESSONS, PATHS, lessons_for_path, public_lesson, public_quiz
from app.core.security import ToolError
from app.tools.util import as_int, required_str


def list_learning_paths(_args: dict | None = None) -> dict:
    paths = []
    for path in sorted(PATHS, key=lambda item: item.order):
        lessons = lessons_for_path(path.id)
        paths.append(
            {
                "id": path.id,
                "title": path.title,
                "summary": path.summary,
                "audience": path.audience,
                "lessons": [
                    {"id": lesson.id, "title": lesson.title, "summary": lesson.summary}
                    for lesson in lessons
                ],
            }
        )
    return {"summary": f"{len(paths)} learning paths", "paths": paths}


def get_lesson(args: dict) -> dict:
    lesson_id = required_str(args, "lesson_id", 64).lower()
    lesson = LESSONS.get(lesson_id)
    if lesson is None:
        raise ToolError(f"No lesson with id {lesson_id}")
    payload = public_lesson(lesson)
    payload["summary"] = f"Lesson: {lesson.title}"
    return payload


def get_quiz(args: dict) -> dict:
    lesson_id = required_str(args, "lesson_id", 64).lower()
    lesson = LESSONS.get(lesson_id)
    if lesson is None:
        raise ToolError(f"No lesson with id {lesson_id}")
    return {
        "summary": f"Quiz for {lesson.title}",
        "lesson_id": lesson.id,
        "title": lesson.title,
        "questions": public_quiz(lesson),
    }


def grade_quiz(args: dict) -> dict:
    lesson_id = required_str(args, "lesson_id", 64).lower()
    lesson = LESSONS.get(lesson_id)
    if lesson is None:
        raise ToolError(f"No lesson with id {lesson_id}")
    raw_answers = args.get("answers")
    if not isinstance(raw_answers, list):
        raise ToolError("answers must be a list of choice indexes")
    if len(raw_answers) != len(lesson.quiz):
        raise ToolError(f"expected {len(lesson.quiz)} answers")
    answers = [as_int(item, "answer", 0, 10) for item in raw_answers]
    results = []
    score = 0
    for question, given in zip(lesson.quiz, answers, strict=True):
        correct = given == question.answer
        score += int(correct)
        results.append(
            {
                "prompt": question.prompt,
                "correct": correct,
                "chosen": given if given < len(question.choices) else None,
                "correct_choice": question.choices[question.answer],
                "explanation": question.explanation,
            }
        )
    return {
        "summary": f"Score {score}/{len(lesson.quiz)} on {lesson.title}",
        "lesson_id": lesson.id,
        "score": score,
        "total": len(lesson.quiz),
        "results": results,
    }


def explain_concept(args: dict) -> dict:
    query = required_str(args, "query", 500).lower()
    scored: list[tuple[int, str]] = []
    for lesson in LESSONS.values():
        score = _score(query, lesson)
        if score:
            scored.append((score, lesson.id))
    scored.sort(key=lambda item: (-item[0], LESSONS[item[1]].order))
    if not scored:
        return {
            "summary": "No curriculum match",
            "query": query,
            "matches": [],
            "note": (
                "No lesson matched. Ask about UTXOs, transactions, scripts, blocks, consensus, "
                "the peer-to-peer network, the mempool, BIPs, Lightning, ACK/NACK, or pull requests."
            ),
        }
    best = LESSONS[scored[0][1]]
    related = []
    for _, lesson_id in scored[1:4]:
        lesson = LESSONS[lesson_id]
        related.append({"id": lesson.id, "title": lesson.title, "summary": lesson.summary})
    return {
        "summary": f"Explained {best.title}",
        "query": query,
        "lesson": public_lesson(best),
        "related": related,
    }


def _score(query: str, lesson) -> int:
    score = 0
    if query == lesson.id or f" {lesson.id} " in f" {query} ":
        score += 12
    if lesson.title.lower() in query:
        score += 8
    terms = lesson.keywords + lesson.concepts + [lesson.id]
    for term in terms:
        if _term_in(query, term.lower()):
            score += 5
    return score


def _term_in(query: str, term: str) -> bool:
    if " " in term:
        return term in query
    return re.search(rf"\b{re.escape(term)}\b", query) is not None
