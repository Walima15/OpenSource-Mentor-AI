"""Small argument parsers shared by tools."""

from __future__ import annotations

from app.core.security import ToolError


def required_str(args: dict, key: str, limit: int = 500) -> str:
    value = args.get(key)
    if not isinstance(value, str):
        raise ToolError(f"{key} is required")
    value = value.strip()
    if not value or len(value) > limit or "\x00" in value:
        raise ToolError(f"{key} must be 1-{limit} characters")
    return value


def optional_str(args: dict, key: str, limit: int = 500) -> str | None:
    value = args.get(key)
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise ToolError(f"{key} must be a string")
    value = value.strip()
    if len(value) > limit or "\x00" in value:
        raise ToolError(f"{key} is too long")
    return value


def as_int(value: object, name: str, lo: int, hi: int) -> int:
    if isinstance(value, bool):
        raise ToolError(f"{name} must be an integer")
    if isinstance(value, str) and value.isdigit():
        value = int(value)
    if not isinstance(value, int):
        raise ToolError(f"{name} must be an integer")
    if value < lo or value > hi:
        raise ToolError(f"{name} must be between {lo} and {hi}")
    return value


def optional_int(args: dict, key: str, lo: int, hi: int) -> int | None:
    if key not in args or args[key] is None or args[key] == "":
        return None
    return as_int(args[key], key, lo, hi)
