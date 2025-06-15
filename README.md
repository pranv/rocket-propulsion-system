# Rocket Propulsion System Simulator

A composable, constraint-based model for rocket engine systems built in Python. This system provides a modular, extensible framework for defining, configuring, and analyzing rocket propulsion systems with automatic performance calculations.

## Features

- **Modular Component Design**: Define tanks, pumps, combustion chambers, nozzles, and other components independently
- **Automatic Constraint Solving**: Uses SymPy to automatically solve thermodynamic and fluid dynamics equations
- **Performance Analysis**: Calculate thrust, specific impulse, mass flow rates, and other key metrics
- **Engineering Validation**: Built-in constraint validation for realistic rocket designs
- **Extensible Architecture**: Easy to add new component types and constraints

## Quick Start

```python
from rocket_system import create_25kn_rocket

# Create a complete 25kN thrust rocket system
rocket = create_25kn_rocket()

# Get performance metrics
print(f"Thrust: {rocket.thrust():.0f} N")
print(f"Specific Impulse: {rocket.specific_impulse():.1f} s")
print(f"Thrust-to-Weight: {rocket.thrust_to_weight_ratio():.2f}")

# Print comprehensive summary
rocket.print_summary()
```

## System Architecture

The simulator is built around several key concepts:

### Components
- **Tank**: Propellant storage with pressure and volume constraints
- **Pump**: Pressurization system with efficiency and power calculations
- **Chamber**: Combustion chamber with thermodynamic performance modeling
- **Nozzle**: Expansion nozzle with isentropic flow calculations
- **Fuel**: Propellant definitions (LOX, LH2, Methane) with physical properties

### Constraint System
The `ConstraintSystem` class uses SymPy to:
- Manage symbolic variables and equations
- Automatically solve complex constraint networks
- Handle thermodynamic relationships
- Calculate derived performance metrics

## Example: 25kN LOX/LH2 Rocket

The included example creates a complete rocket system:

- **Propellants**: Liquid Oxygen (LOX) and Liquid Hydrogen (LH2)
- **Target Thrust**: 25,000 N
- **Chamber Pressure**: 10 MPa
- **Expansion Ratio**: 25:1
- **O/F Ratio**: ~6:1 (optimized for LH2/LOX)

### Performance Results
- Thrust: ~25,000 N
- Specific Impulse: ~420 s
- Exit Velocity: ~4,120 m/s
- Total Mass Flow Rate: 8.4 kg/s

## Component Details

### Fuel Types
```python
# Built-in propellant definitions
lox = LOX()        # Liquid Oxygen
lh2 = LH2()        # Liquid Hydrogen  
methane = Methane() # Liquid Methane
```

### Tank System
```python
fuel_tank = Tank(
    fuel=lh2,
    mass=40.0,      # kg
    volume=0.4,     # m³
    pressure=2e6    # Pa
)
```

### Turbopump System
```python
fuel_pump = Pump(
    pressure_gain=8e6,    # 8 MPa boost
    efficiency=0.75,      # 75% efficient
    mass_flow_rate=1.2,   # kg/s
    fluid_density=lh2.density
)
```


## Requirements

```bash
pip install sympy
```

## Running the Simulator

```bash
python rocket_system.py
```

This will run the complete test suite and display:
- System performance summary
- Constraint validation results
- Component-level analysis

## Extending the System

### Adding New Components
```python
@dataclass(slots=True)
class MyComponent(Component):
    custom_parameter: Float = None
    
    def add_constraints(self, cs: 'ConstraintSystem'):
        # Add your constraints here
        if self.custom_parameter:
            cs.add_variable('custom_param', self.custom_parameter)
```

### Adding New Constraints
```python
# In your component's add_constraints method
cs.add_constraint(Eq(thrust_var, mass_flow * exit_velocity))
```

## Applications

This simulator is useful for:
- **Rocket Design**: Preliminary sizing and performance estimation
- **Education**: Understanding rocket thermodynamics and constraints
- **Research**: Exploring trade-offs in propulsion system design
- **Validation**: Checking feasibility of rocket configurations

## Technical Background

The simulator implements fundamental rocket equations:
- **Rocket Equation**: F = ṁ × Ve + (Pe - Pa) × Ae
- **Isentropic Flow**: For nozzle expansion calculations
- **Pump Power**: P = Δp × V̇ / η
- **Mass Conservation**: Propellant flow balance
- **Energy Conservation**: Thermodynamic cycle analysis
