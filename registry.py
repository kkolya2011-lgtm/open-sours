from typing import Callable, Awaitable
from dataclasses import dataclass

@dataclass
class Plugin:
    name: str
    description: str
    kinds: tuple[str, ...]
    handler: Callable[..., Awaitable[str]]

REGISTRY: dict[str, Plugin] = {}

def plugin(name: str, description: str, kinds: tuple[str, ...]):
    def deco(fn):
        REGISTRY[name] = Plugin(name, description, kinds, fn)
        return fn
    return deco

def for_kind(kind: str) -> list[Plugin]:
    return [p for p in REGISTRY.values() if kind in p.kinds]
