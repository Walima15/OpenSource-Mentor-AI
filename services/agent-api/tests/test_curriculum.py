"""Curriculum content and quiz grading."""

from __future__ import annotations

from app.content.loader import LESSONS, PATHS, lessons_for_path
from app.tools.curriculum import explain_concept, grade_quiz, list_learning_paths


def test_catalog_is_consistent():
    path_ids = {path.id for path in PATHS}
    assert path_ids == {"bitcoin-fundamentals", "lightning", "contribution-craft"}
    for path in PATHS:
        lessons = lessons_for_path(path.id)
        assert lessons, path.id
        orders = [lesson.order for lesson in lessons]
        assert orders == sorted(orders)
        assert len(orders) == len(set(orders))
    for lesson in LESSONS.values():
        assert lesson.body.strip()
        for question in lesson.quiz:
            assert 0 <= question.answer < len(question.choices)
            assert question.explanation


def test_explain_utxo_lesson():
    result = explain_concept({"query": "Explain UTXOs"})
    lesson = result["lesson"]
    assert lesson["id"] == "utxos"
    assert "unspent" in lesson["body"].lower()
    assert "answer" not in lesson["quiz"][0]


def test_ack_concept_finds_review_culture():
    result = explain_concept({"query": "How do ACK and NACK work?"})
    assert result["lesson"]["id"] == "review-culture"
    assert "Concept ACK" in result["lesson"]["body"]


def test_grade_quiz_scores_correct_and_wrong_answers():
    lesson = LESSONS["utxos"]
    correct = [question.answer for question in lesson.quiz]
    graded = grade_quiz({"lesson_id": "utxos", "answers": correct})
    assert graded["score"] == len(correct)
    wrong = [0 if answer != 0 else 1 for answer in correct]
    graded_wrong = grade_quiz({"lesson_id": "utxos", "answers": wrong})
    assert graded_wrong["score"] == 0
    assert graded_wrong["results"][0]["explanation"]


def test_paths_cover_required_topics():
    payload = list_learning_paths({})
    titles = " ".join(
        lesson["title"] + " " + lesson["summary"]
        for path in payload["paths"]
        for lesson in path["lessons"]
    ).lower()
    for topic in (
        "utxo",
        "transaction",
        "script",
        "block",
        "consensus",
        "peer",
        "mempool",
        "bip",
        "lightning",
        "ack",
        "signed",
        "pull request",
        "mailing",
        "irc",
    ):
        assert topic in titles or topic in " ".join(lesson.id for lesson in LESSONS.values())


def test_unknown_concept_does_not_invent_a_lesson():
    result = explain_concept({"query": "quantum origami knitting"})
    assert result["matches"] == [] or result.get("lesson") is None
    assert "lesson" not in result
