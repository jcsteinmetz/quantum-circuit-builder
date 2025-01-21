from abc import ABC, abstractmethod

class Component(ABC):
    @abstractmethod
    def __init__(self, backend):
        self.backend = backend
        self.validate()

    @abstractmethod
    def apply(self):
        raise NotImplementedError
    
    @abstractmethod
    def validate(self):
        raise NotImplementedError
    
    def validate_beamsplitter(self, wires, theta):
        self.validate_wires(wires, 2)
        self.validate_angle(theta)

    def validate_switch(self, wires):
        self.validate_wires(wires, 2)

    def validate_phaseshift(self, wires, phase):
        self.validate_wires(wires, 1)
        self.validate_angle(phase)

    def validate_loss(self, wires, eta):
        self.validate_wires(wires, 1)
        self.validate_transmission(eta)

    def validate_detector(self, wires, herald):
        self.validate_wires(wires, 1)
        self.validate_herald(herald)

    def validate_angle(self, angle):
        if not isinstance(angle, (int, float)):
            raise TypeError("Angle must be a number.")
        if not (0 <= angle <= 180):
            raise ValueError("Angle must be between 0 and 180 degrees.")
        
    def validate_transmission(self, transmission):
        if not isinstance(transmission, (int, float)):
            raise TypeError("Transmission must be a number.")
        if not (0 <= transmission <= 1):
            raise ValueError("Transmission must be between 0 and 1.")
        
    def validate_herald(self, herald):
        if not isinstance(herald, list):
            raise TypeError("Herald must be a list.")
        if len(herald) != 1:
            raise ValueError("Herald must contain exactly 1 element.")
        if not all(isinstance(h, int) for h in herald):
            raise TypeError("All elements in herald must be integers.")
        if not all(0 <= h <= self.backend.n_photons for h in herald):
            raise ValueError(f"Herald must be between 0 and {self.backend.n_photons}.")
        
    def validate_wires(self, wires, length):
        if not isinstance(wires, list):
            raise TypeError("Wires must be a list.")
        if len(wires) != length:
            raise ValueError(f"Wires must contain exactly {length} elements.")
        if not all(isinstance(wire, int) for wire in wires):
            raise TypeError("All elements in wires must be integers.")
        if len(set(wires)) != length:
            raise ValueError("Wires must not contain duplicate integers.")
        if not all(1 <= wire <= self.backend.n_wires for wire in wires):
            raise ValueError(f"Each wire must be an integer between 1 and {self.backend.n_wires}.")
        
    def validate_qubits(self, qubits, length):
        if not isinstance(qubits, list):
            raise TypeError("Qubits must be a list.")
        if len(qubits) != length:
            raise ValueError(f"Qubits must contain exactly {length} elements.")
        if not all(isinstance(qubit, int) for qubit in qubits):
            raise TypeError("All elements in qubits must be integers.")
        if len(set(qubits)) != length:
            raise ValueError("Qubits must contain two distinct integers.")
        if not all(1 <= qubit <= self.backend.n_qubits for qubit in qubits):
            raise ValueError(f"Each qubit must be an integer between 1 and {self.backend.n_qubits}.")