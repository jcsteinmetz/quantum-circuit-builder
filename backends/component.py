from abc import ABC, abstractmethod

class Component(ABC):
    @abstractmethod
    def __init__(self, backend):
        self.backend = backend
        self.validate_input()

    def apply(self):
        raise NotImplementedError
    
    def validate_input(self):
        raise NotImplementedError