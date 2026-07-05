"""Tests for settings-derived helpers."""

from __future__ import annotations

from app.core.config import Settings


def test_cors_origin_list_splits_and_strips():
    settings = Settings(cors_origins="http://a.com, http://b.com ,http://c.com")
    assert settings.cors_origin_list == [
        "http://a.com",
        "http://b.com",
        "http://c.com",
    ]


def test_cors_origin_list_ignores_blanks():
    settings = Settings(cors_origins="http://a.com,, ,")
    assert settings.cors_origin_list == ["http://a.com"]


def test_is_production_is_case_insensitive():
    assert Settings(app_env="production").is_production
    assert Settings(app_env="Production").is_production
    assert not Settings(app_env="development").is_production
