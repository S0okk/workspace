# def binary_search(a, target):
#     left, right = 0, len(a) - 1
#     while left <= right:
#         mid = (left + right) // 2
#         if a[mid] == target:
#             return mid
#         elif a[mid] < target:
#             left = mid + 1
#         else:
#             right = mid - 1
#     return -1
# print(binary_search([1, 2, 3, 4, 5], 1))

# import heapq
# a = [3, 1, 4, 1, 5]
# heapq.heapify(a) # превратить список в кучy
# heapq.heappush(a, 2) # добавить
# smallest = heapq.heappop(a)
# heapq.heappop(a)# извлечь минимальный

# def k_smallest(arr, k):
#     heapq.heapify(arr)
#     for i in range(len(arr) - 1):
#         if heapq.heappop(arr) == k:
#             return i
# a = [3, 1, 4, 1, 5, 9, 2, 6, 5]
# heapq.heapify(a)
# print(a)
# print(k_smallest(a, 5))

# def is_almost_sorted(a, k):
#     n = len(a)
#     tmp = a.copy()
#     heapq.heapify(tmp)
#     for i in range(n - 1):
#         if a[i] - heapq.heappop(tmp) > k:
#             return False
#     return True

class Typed:
    def __init__(self, name, typ):
        self.name = name
        self.typ = typ

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return instance.__dict__[self.name]

    def __set__(self, instance, value):
        if not isinstance(value, self.typ):
            raise TypeError(f"{self.name} must be {self.typ}")
        instance.__dict__[self.name] = value

# class Person:
#     age = Typed("age", int)
#     def __init__(self, age):
#         self.age = age
    
#     def show_age(self):
#         return self.age

# p = Person(10)
# p.age = 31
# print(p.show_age())
# p.age = "30"  # TypeError

class Person:
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        # getter: может форматировать/отдавать копию
        return self._name.capitalize()

    @name.setter
    def name(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("name must be non-empty")
        self._name = value.strip()

    @name.deleter
    def name(self):
        raise AttributeError("can't delete name")

p = Person(" alice ")
# print(p.name)  # "Alice"
p.name = " frank    "
# del p.name # AttributeError
# print(p.name)

from functools import cached_property  # noqa: E402

class DataLoader:
    @cached_property
    def expensive(self):
        print("compute once")
        return sum(range(100_000_000))

d = DataLoader()
# print(d.expensive)  # compute printed once
# print(d.expensive)  # cached


from dataclasses import dataclass  # noqa: E402

@dataclass
class Point:
    x: float
    y: float

p = Point(1.0, 2.0)
# print(p)  # Point(x=1.0, y=2.0)

@dataclass
class Rect:
    width: float
    height: float

    @property
    def area(self) -> float:
        return self.width * self.height

r = Rect(3.0, 4.0)
# print(r.area)  # 12.0

from dataclasses import dataclass  # noqa: E402

@dataclass(frozen=True)
class ID:
    id_str: str
    cleaned: str = None

    def __post_init__(self):
        object.__setattr__(self, "cleaned", self.id_str.strip())

id1 = ID("  ABC123  ")
print(id1.cleaned)  # "ABC123"