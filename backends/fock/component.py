from abc import ABC, abstractmethod

class Component(ABC):
    def __init__(self, state):
        self.state = state

    @abstractmethod
    def unitary(self):
        raise NotImplementedError
