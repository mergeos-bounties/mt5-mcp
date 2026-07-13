from __future__ import annotations

import os
from typing import Literal

Mode = Literal["mock", "live"]
_PREFIX = "MT5_MCP"


def get_mode() -> Mode:
    raw = (os.environ.get(f"{_PREFIX}_MODE") or "mock").strip().lower()
    return "live" if raw == "live" else "mock"


def set_mode(mode: str) -> Mode:
    m: Mode = "live" if mode.strip().lower() == "live" else "mock"
    os.environ[f"{_PREFIX}_MODE"] = m
    return m


def bridge_url() -> str | None:
    v = (os.environ.get(f"{_PREFIX}_BRIDGE_URL") or "").strip()
    return v or None


def bridge_file() -> str | None:
    v = (os.environ.get(f"{_PREFIX}_BRIDGE_FILE") or "").strip()
    return v or None


def magic_number() -> int | None:
    v = os.environ.get("MT5_MCP_MAGIC")
    return int(v) if v else None

def max_volume() -> float:
    v = os.environ.get("MT5_MCP_MAX_VOLUME")
    return float(v) if v else 100.0

def symbol_allowlist() -> list[str] | None:
    v = os.environ.get("MT5_MCP_SYMBOL_ALLOWLIST")
    return [s.strip() for s in v.split(",") if s.strip()] if v else None
