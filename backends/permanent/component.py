from abc import ABC, abstractmethod

class Component(ABC):
    def __init__(self, circuit):
        self.circuit = circuit

    @abstractmethod
    def apply(self):
        raise NotImplementedError
