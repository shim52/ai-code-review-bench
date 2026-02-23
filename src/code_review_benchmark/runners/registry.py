"""Tool discovery and registration."""

from __future__ import annotations

from code_review_benchmark.runners.base import AbstractToolRunner

_REGISTRY: dict[str, type[AbstractToolRunner]] = {}


def register_tool(cls: type[AbstractToolRunner]) -> type[AbstractToolRunner]:
    """Class decorator to register a tool runner."""
    instance = cls()
    _REGISTRY[instance.name] = cls
    return cls


def get_runner(name: str) -> AbstractToolRunner:
    cls = _REGISTRY.get(name)
    if cls is None:
        raise KeyError(f"Unknown tool: {name}. Available: {list(_REGISTRY)}")
    return cls()


def list_runners() -> list[AbstractToolRunner]:
    return [cls() for cls in _REGISTRY.values()]


def available_tool_names() -> list[str]:
    return list(_REGISTRY.keys())
