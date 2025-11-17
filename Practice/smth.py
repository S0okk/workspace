#посмортеть int is == с 256-го числа
#C3 алгоритм линеризации
#mro как работает
#патерны проеткирования


from dataclasses import dataclass, field
from functools import cached_property


class Person:
    def __init__(self, email):
        if not email:
            raise ValueError("Email cannot be empty")
        self._email = email.lower()
    
    @property
    def email(self):
        return self._email
    
    @email.setter
    def email(self, value):
        if not value:
            raise ValueError("Email cannot be empty")
        else:
            self._email = value.lower()

# person = Person("my@eMail@.com")
# print(person.email)
# person.email = "anothER@gmail.com"
# print(person.email)
# person.email = ""
# print(person.email)

class Matrix:
    def __init__(self, matrix):
        self.matrix = matrix
    # Only 2 * 2 matrix
    @cached_property
    def det(self):
        print("Calculating determinant...")
        return self.matrix[0][0] * self.matrix[1][1] - self.matrix[0][1] * self.matrix[1][0]

@dataclass(frozen=True)
class Config:
    host: str # host already str
    port: int
    debug: bool = False
    
    def __post_init__(self):
        object.__setattr__(self, 'host', self.host.strip())


@dataclass
class Bag:
    items: list = field(default_factory=list)
    
    def add_value(self, value):
        self.items.append(value)
    
    def total(self):
        return sum(self.items)

class User:
    def __init__(self, name):
        self.name = name
    
    @classmethod
    def from_dict(cls, data):
        return cls(data['name'])

class Slug:
    
    @staticmethod
    def normalize(text):
        result = text.lower().replace(" ", "-").strip("-")
        return result
    
    @classmethod
    def from_title(cls, title):
        normalized = cls.normalize(title)
        return normalized

class X:
    def show(self):
        print("X")

class Y(X):
    def show(self):
        super().show()

class Z(X):
    def show(self):
        super().show()

class W(Y, Z):
    def show(self):
        super().show()

w = W()
w.show()