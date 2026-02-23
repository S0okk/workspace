def cacheable(func):
    func._is_cacheable = True
    return func


class CacheMixin:
    def __init__(self):
        self._cache = {}
        
    def __getattribute__(self, name):
        attr = super().__getattribute__(name)
        
        if callable(attr) and getattr(attr, '_is_cacheable', False):
            def wrapper(*args):
                if args in self._cache:
                    return self._cache[args]
                result = attr(*args)
                self._cache[args] = result
                return result
            return wrapper
        return attr

class MathOps(CacheMixin):
    def __init__(self):
        super().__init__()

    @cacheable
    def fib(self, n):
        if n <= 1:
            return n
        return self.fib(n - 1) + self.fib(n - 2)
    
    def non_cached_fib(self, n):
        if n <= 1:
            return n
        return self.non_cached_fib(n - 1) + self.non_cached_fib(n - 2)

m = MathOps()
print(m.fib(50)) # very fast
print(m.non_cached_fib(50)) # extremly slow

class User:
    def __init__(self, user):
        self.user = user

class UserFormat(User):
    def format_user(self):
        return f"{self.user['id']}: {self.user['name']}"

class UserSave(User):
    def save(self, content: str, path: str):
        with open(path, "w") as f:
            f.write(content)

class UserSend(User):
    def send(self, content: str, addr: str):
        print(f"Send to {addr}: {content}")


class ExportOrderCSV:
    def export(self, content: str):
        return content.replace(" - ", ",") 


class ExportOrderJSON:
    def export(self, content: str):
        lines = content.split("\n")
        items = []
        for line in lines:
            id_, total = line.split(" - ")
            items.append({"id": id_, "total": total})
        import json
        return json.dumps(items)


from abc import ABC, abstractmethod

class ShippingStrategy(ABC):
    @abstractmethod
    def shipping_cost(self):
        pass


class ShippingCostAir(ShippingStrategy):
    def shipping_cost(self):
        return 20


class ShippingCostGround(ShippingStrategy):
    def shipping_cost(self):
        return 5


class File(ABC):
    pass

class Readable(ABC):
    @abstractmethod
    def read(self):
        pass

class Writable(ABC):
    @abstractmethod
    def write(self, data: str):
        pass


class FileWriter(Writable):
    def write(self, data: str):
        print(f"Writing in file {data}")

class ReadOnlyFile(Readable):
    def read(self):
        print("Reading file")


class Bird(ABC): 
    pass

class FlyingBird(Bird):
    @abstractmethod
    def fly(self):
        pass

class WalkingBird(Bird):
    @abstractmethod
    def walk(self):
        pass

class Penguin(WalkingBird):
    def walk(self):
        print("Penguin is walking")


class Payment(ABC):
    @abstractmethod
    def pay(self, amount):
        pass

class CryptoPayment(Payment):
    pass

class BinancePayment(CryptoPayment):
    def pay(self, amount):
        print(f"Paying with Binance: {amount}")

    def check_minimum(self, amount):
        return amount >= 100


class Database(ABC):
    @abstractmethod
    def write(self, data):
        pass

    @abstractmethod
    def read(self, key):
        pass


class MySQLDatabase(Database):
    def write(self, data):
        print("write to MySQL", data)

    def read(self, key):
        print("read from MySQL", key)


class UserRepository:
    def __init__(self, db: Database):
        self.db = db



class Notifier(ABC):
    @abstractmethod
    def send(self, message: str):
        pass


class SMSNotifier(Notifier):
    def send(self, message: str):
        print("SMS:", message)


class EmailNotifier(Notifier):
    def send(self, message: str):
        print("Email:", message)


class PaymentService:
    def process(self, notifier: Notifier):
        notifier.send("ok")



class Logger(ABC):
    @abstractmethod
    def log(self, msg: str):
        pass


class FileLogger(Logger):
    def log(self, msg: str):
        print("LOG:", msg)


class OrderProcessor:
    def process(self, order, logger: Logger):
        logger.log("start")
