[![Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue)](https://opensource.org/licenses/Apache-2.0)

Quantum Circuit Builder is a GUI for designing and simulating quantum linear optical circuits. It consolidates various open-source quantum simulators into a common API, allowing easy comparison and benchmarking.

## Key features
* Easy, intuitive way to design new circuits by drawing components on an interactive canvas
* Simulate the state probabilities generated by new circuit diagrams
* Includes both gate-based and photonic simulators
* Save and load circuit designs
* Benchmark performance metrics for different industry simulators

## List of implemented backends
### Photonic
* `FockBackend`: Fock space demo backend
* `PermanentBackend`: Matrix permanent demo backend
* `MrMustardBackend`: [MrMustard](https://github.com/XanaduAI/MrMustard) backend
* `PercevalBackend`: [Perceval](https://github.com/Quandela/Perceval) Naive backend
### Gate-based
* `MPBackend`: Matrix product demo backend
* `QiskitBackend`: [Qiskit](https://github.com/qiskit) density matrix backend

## Installation

Clone the repository using
```
git clone https://github.com/jcsteinmetz/quantum-circuit-designer
cd quantum-circuit-designer
```
then install the requirements by running
```
pip install -r requirements.txt
```

## Usage
To use the GUI, run 
```
main.py
```
. It is also possible to create a circuit without using the GUI, which is useful if you want to iterate over circuits or benchmark different backends. The same syntax is used to access all backends, with slight differences between gate-based and photonic backends. 

### Gate-based circuits
To create a gate-based circuit using the matrix product demo backend, we create a MatrixProduct object with a number of qubits:
```
from backends import MatrixProduct

circuit = MPBackend(n_qubits = 2)
```
The initial state is entered as a list of zeros and ones, which are the initial states of each qubit. For example, to input both qubits in the zero state, use
```
circuit.set_input_state((0, 0))
```
Currently, more complicated input states like superpositions must be created with components.

Qubits are 1-indexed, so the following adds an X-gate to the first qubit and a Hadamard to the second qubit:
```
circuit.add_xgate(qubit = 1)
circuit.add_hadamard(qubit = 2)
```
Finally, we run the circuit
```
circuit.run()
```
To access the results, use the property
```
circuit.output_data
```
which is a table containing each basis state and its associated probability, which is the table displayed in the output tab of the GUI.

### Photonic circuits
The main difference with photonic circuits is that instead of giving the backend the number of qubits, we give it the number of wires and photons. For example, to create a circuit in the Fock space demo backend that is analogous to the circuit we just created, use
```
circuit = FockBackend(n_wires = 4, n_photons = 2)
```
The input state is a Fock state, which is the number of photons in each wire,
```
circuit.set_input_state((1, 0, 1, 0))
```
This creates two dual-rail photonic qubits in the zero state.

The rest of the syntax is the same as for gate-based circuits, just with a different set of components. For example, we can add beam splitters, phase shifters, or loss:
```
circuit.add_beamsplitter(wires = [1, 3])
circuit.add_phaseshift(wire = 1)
circuit.add_loss(wire = 1, eta = 0.9)
circuit.run()
print(circuit.output_data)
```
Like qubits, wires are 1-indexed. Certain components have optional parameters that can assist in modelling errors or non-standard components. For example, we can create a beam splitter that is unbalanced by ten degrees using
```
circuit.add_beamsplitter(wires = [1, 3], theta = 170)
```
These properties are also shown in the GUI when a component is selected.

If ever in doubt about the code to create a specific circuit, you can also use the GUI to create the circuit and the corresponding lines of code will be displayed in the console. There is also a notebook `benchmark.ipynb` showing runtime comparisons for different photonic backends.

## Screenshot
![](assets/screenshot.png)
