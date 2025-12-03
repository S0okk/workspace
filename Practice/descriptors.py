from abc import ABC, abstractmethod

class ExportReport(ABC):
    @abstractmethod
    def export_to(self):
        pass