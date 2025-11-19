class UpperCaseMixin:
    def to_upper(self, text: str):
        print(text.upper())

class Message(UpperCaseMixin):
    def show(self, text: str):
        self.to_upper(text)

mes = Message()
# mes.show("message")


class CounterMixin:
    def __init__(self) -> None:
        self.calls = 0
    def run(self):
        self.calls += 1
        print(f"Calls: {self.calls}")

class Processor(CounterMixin):
    def run(self):
        super().run()

pr = Processor()
# pr.run()
# pr.run()
# pr.run()

class SafeExecuteMixin:
    def execute(self, func, *args, **kwargs):
        try:
            func(self, *args, **kwargs)
        except Exception:
            print("Error")

class Task:
    def execute(self) -> None:
        raise ValueError

class SafeTask(SafeExecuteMixin, Task):
    def execute(self, func, *args, **kwargs):
        return super().execute(func, *args, **kwargs)

# safe_task = SafeTask()
# task = Task()
# safe_task.execute(task.execute)


class LoggerMixin:
    def log(self, message: str):
        print(f'[LOG]: {message}')


import time  # noqa: E402
class TimingMixin:
    def time_log(self, func):
        start = time.time()
        result = func()
        end = time.time()
        print(f"Execution time: {end - start} seconds")
        return result

class Worker(LoggerMixin, TimingMixin):
    def work(self):
            time.sleep(1)
    def perform(self):
        self.log("Starting work")
        self.time_log(self.work)
        self.log("Work completed")

worker = Worker()
worker.perform()

import json # noqa: E402
class JsonSerializableMixin:
    __serializable_fields__ = ["id", "name"]
    def __init__(self, id, name, password):
        self.id = id
        self.name = name
        self.password = password
    
    def to_json(self):
                    