"""Seed demo data for local development.

Creates a demo profile and a couple of tracked repositories so the dashboard has
content without going through the full GitHub flow. Intended for local/dev use.

Usage:
    python -m scripts.seed
"""

from __future__ import annotations

import uuid

from app.db.models import IndexStatus, Skill, SkillLevel, TrackedRepo
from app.db.models import Profile
from app.db.session import SessionLocal

DEMO_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def main() -> None:
    db = SessionLocal()
    try:
        profile = db.get(Profile, DEMO_USER_ID)
        if profile is None:
            profile = Profile(
                id=DEMO_USER_ID,
                github_username="demo-dev",
                bio="Demo account for local development.",
            )
            db.add(profile)
            db.flush()

        if not profile.skills:
            db.add_all(
                [
                    Skill(
                        user_id=DEMO_USER_ID,
                        language="Python",
                        level=SkillLevel.intermediate,
                        score=70,
                    ),
                    Skill(
                        user_id=DEMO_USER_ID,
                        language="TypeScript",
                        level=SkillLevel.beginner,
                        score=40,
                    ),
                ]
            )

        demo_repos = [
            ("pallets", "flask", "The Python micro web framework.", 67000, "Python"),
            ("tiangolo", "fastapi", "Modern, fast web framework for APIs.", 78000, "Python"),
        ]
        for owner, name, desc, stars, language in demo_repos:
            exists = (
                db.query(TrackedRepo)
                .filter_by(user_id=DEMO_USER_ID, owner=owner, name=name)
                .first()
            )
            if not exists:
                db.add(
                    TrackedRepo(
                        user_id=DEMO_USER_ID,
                        owner=owner,
                        name=name,
                        description=desc,
                        primary_language=language,
                        stars=stars,
                        default_branch="main",
                        index_status=IndexStatus.pending,
                    )
                )

        db.commit()
        print("Seeded demo data for user", DEMO_USER_ID)
    finally:
        db.close()


if __name__ == "__main__":
    main()
