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

class Person:
    age = Typed("age", int)
    def __init__(self, age):
        self.age = age
    
    def show_age(self):
        return self.age

p = Person(30)
p.age = 31
print(p.show_age())
# p.age = "30"  # TypeError