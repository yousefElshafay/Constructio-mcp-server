"""MCP tooling for the API package."""

from __future__ import annotations

from importlib.machinery import PathFinder
from importlib.util import module_from_spec
from pathlib import Path
from pkgutil import extend_path
from types import ModuleType
import sys

__path__ = extend_path(__path__, __name__)

_external_mcp: ModuleType | None = None
_loading_external = False


def _load_external_mcp() -> ModuleType:
    global _external_mcp, _loading_external
    if _external_mcp is not None:
        return _external_mcp
    if _loading_external:
        if _external_mcp is not None:
            return _external_mcp
        raise ImportError("External 'mcp' package is still initializing.")

    local_api_path = str(Path(__file__).resolve().parents[1])
    search_paths = [path for path in sys.path if path != local_api_path]
    spec = PathFinder.find_spec(__name__, search_paths)
    if spec is None or spec.loader is None:
        raise ImportError("External 'mcp' package could not be located.")

    module = module_from_spec(spec)
    _external_mcp = module
    _loading_external = True
    spec.loader.exec_module(module)
    _loading_external = False
    if spec.submodule_search_locations:
        for location in spec.submodule_search_locations:
            if location not in __path__:
                __path__.append(location)

    _external_mcp = module
    return module


def __getattr__(name: str):
    external = _load_external_mcp()
    return getattr(external, name)


def __dir__() -> list[str]:
    external = _load_external_mcp()
    return sorted(set(globals().keys()) | set(dir(external)))
