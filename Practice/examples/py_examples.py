"""Small curated Python examples collected and documented.

Run individual examples with `python -m workspace.Practice.examples.py_examples` or directly.
"""

from dataclasses import dataclass, field
from functools import cached_property


class Person:
    """Simple Person with email validation."""

    def __init__(self, email: str):
        if not email:
            raise ValueError("Email cannot be empty")
        self._email = email.lower()

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        if not value:
            raise ValueError("Email cannot be empty")
        self._email = value.lower()


class Matrix2x2:
    """2x2 matrix with cached determinant calculation."""

    def __init__(self, values: list[list[float]]):
        self.values = values

    @cached_property
    def det(self) -> float:
        a, b = self.values[0]
        c, d = self.values[1]
        return a * d - b * c


@dataclass(frozen=True)
class Config:
    host: str
    port: int
    debug: bool = False

    def __post_init__(self):
        object.__setattr__(self, "host", self.host.strip())


def demo():
    p = Person("User@Example.COM")
    print("Normalized email:", p.email)

    m = Matrix2x2([[1, 2], [3, 4]])
    print("Determinant:", m.det)

    cfg = Config(host=" localhost ", port=8000)
    print("Config host:", cfg.host)


if __name__ == "__main__":
    demo()
