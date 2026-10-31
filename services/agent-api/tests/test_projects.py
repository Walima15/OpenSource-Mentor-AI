"""Curated project guides."""

from __future__ import annotations

from app.content.loader import PROJECTS
from app.tools.projects import get_project_guide, list_projects, match_project


def test_catalog_includes_the_main_bitcoin_projects():
    slugs = set(PROJECTS)
    assert {
        "bitcoin-core",
        "bdk",
        "ldk",
        "rust-bitcoin",
        "lnd",
        "core-lightning",
        "btcpay",
        "bolts",
        "secp256k1",
    } <= slugs
    listed = list_projects({})
    assert any(item["slug"] == "bitcoin-core" for item in listed["projects"])


def test_bitcoin_core_guide_has_build_and_review_norms():
    guide = get_project_guide({"project": "bitcoin-core"})
    text = " ".join(guide["setup_steps"] + guide["test_steps"] + guide["contributing"])
    assert "cmake" in text
    assert "ACK" in text
    assert guide["owner"] == "bitcoin"
    assert guide["repo"] == "bitcoin"
    assert any(link["url"].startswith("https://") for link in guide["docs"])


def test_match_project_names():
    assert match_project("good first issues in rust-bitcoin").slug == "rust-bitcoin"
    assert match_project("How do I build Bitcoin Core?").slug == "bitcoin-core"
    assert match_project("plan a contribution to BDK").slug == "bdk"
    assert match_project("Core Lightning channel open").slug == "core-lightning"


def test_unknown_project_is_rejected():
    from app.core.security import ToolError

    try:
        get_project_guide({"project": "not-a-real-project"})
    except ToolError as exc:
        assert "Unknown project" in exc.message
    else:
        raise AssertionError("expected ToolError")
