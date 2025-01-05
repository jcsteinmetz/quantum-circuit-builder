from abc import ABC, abstractmethod

class Backend(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def run(self):
        raise NotImplementedError

    @abstractmethod
    def add_beamsplitter(self, **kwargs):
        raise NotImplementedError
    
    @abstractmethod
    def add_switch(self, **kwargs):
        raise NotImplementedError
