"""Design patterns and utility examples (moved from ad-hoc examples).

Includes: simple caching decorator, strategy example, and file helpers.
"""

from functools import wraps
from typing import Callable, Dict, Tuple


def cacheable(func: Callable) -> Callable:
    """Decorator marking function results as cacheable (simple in-memory cache)."""
    cache: Dict[Tuple, object] = {}

    @wraps(func)
    def wrapper(*args, **kwargs):
        key = args + tuple(sorted(kwargs.items()))
        if key in cache:
            return cache[key]
        result = func(*args, **kwargs)
        cache[key] = result
        return result

    return wrapper


class ShippingStrategy:
    def shipping_cost(self) -> float:
        raise NotImplementedError


class AirShipping(ShippingStrategy):
    def shipping_cost(self) -> float:
        return 20.0


class GroundShipping(ShippingStrategy):
    def shipping_cost(self) -> float:
        return 5.0


def write_text(path: str, content: str) -> None:
    with open(path, "w", encoding="utf8") as f:
        f.write(content)


def demo_cache():
    @cacheable
    def fib(n: int) -> int:
        if n <= 1:
            return n
        return fib(n - 1) + fib(n - 2)

    print("fib(20)", fib(20))


if __name__ == "__main__":
    demo_cache()
