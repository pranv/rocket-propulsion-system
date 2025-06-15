"""
A composable model for rocket systems.

This module provides classes to define, configure, and analyze rocket
engine systems in a modular, extensible way. Each part (tanks, pumps,
combustion chambers, turbines, etc.) is represented as a Component.
Components are assembled into a PropulsionSystem, which builds and solves
symbolic constraints to infer performance metrics like thrust and Isp.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Callable, List
import sympy as sp
from sympy import symbols, Eq, solve
import math

# Standard gravity
G0 = 9.80665  # m/s^2

# Type alias
Float = Optional[float]

@dataclass(slots=True)
class Component:
    mass: Float = None
    volume: Float = None
    density: Float = None

    def add_constraints(self, cs: 'ConstraintSystem'):
        """Override in subclasses to add component-specific constraints"""
        pass

@dataclass(slots=True)
class Fuel(Component):
    molecular_mass: Float = None
    boiling_point: Float = None
    combustion_temperature: Float = None
    specific_heat: Float = None

    def R(self) -> Float:
        """Specific gas constant R = universal gas constant / molecular mass"""
        if self.molecular_mass:
            return 8314.5 / self.molecular_mass
        return None

@dataclass(slots=True)
class Fluid(Component):
    pressure: Float = None
    temperature: Float = None

# Propellants with concise class-level definitions
class LOX(Fuel):
    def __init__(self):
        super().__init__()
        self.molecular_mass = 32.0; self.boiling_point = 90.19; self.combustion_temperature = 3500.0
        self.specific_heat = 1700.0; self.density = 1141.0

class LH2(Fuel):
    def __init__(self):
        super().__init__()
        self.molecular_mass = 2.016; self.boiling_point = 20.28; self.combustion_temperature = 3500.0
        self.specific_heat = 14300.0; self.density = 70.8

class Methane(Fuel):
    def __init__(self):
        super().__init__()
        self.molecular_mass = 16.04; self.boiling_point = 111.65; self.combustion_temperature = 3500.0
        self.specific_heat = 2200.0; self.density = 422.8

@dataclass(slots=True)
class Tank(Component):
    fuel: Optional[Fuel] = None
    pressure: Float = None

    def add_constraints(self, cs: 'ConstraintSystem'):
        if self.pressure:
            cs.add_variable('tank_pressure', self.pressure)

@dataclass(slots=True)
class Pump(Component):
    pressure_gain: Float = None
    efficiency: Float = None
    mass_flow_rate: Float = None
    fluid_density: Float = None

    def add_constraints(self, cs: 'ConstraintSystem'):
        if self.pressure_gain:
            cs.add_variable('pump_pressure_gain', self.pressure_gain)
        if self.mass_flow_rate:
            cs.add_variable('pump_mass_flow_rate', self.mass_flow_rate)

    @property
    def power(self) -> Float:
        """Calculate pump power requirement: P = Δp * (ṁ / ρ) / η"""
        if self.pressure_gain and self.mass_flow_rate and self.fluid_density and self.efficiency:
            volumetric = self.mass_flow_rate / self.fluid_density
            return self.pressure_gain * volumetric / self.efficiency
        return None

@dataclass(slots=True)
class Injector:
    efficiency: Float = None
    pressure_loss: Float = None
    design_type: Optional[str] = None

@dataclass(slots=True)
class Throat:
    area: Float = None  # m^2

@dataclass(slots=True)
class Chamber(Component):
    injector: Optional[Injector] = None
    pressure: Float = None
    throat: Optional[Throat] = None
    temperature: Float = None
    mass_flow_rate: Float = None

    def add_constraints(self, cs: 'ConstraintSystem'):
        # Register chamber variables
        cs.add_variable('chamber_pressure', self.pressure)
        cs.add_variable('chamber_temperature', self.temperature)
        if self.throat and self.throat.area:
            cs.add_variable('throat_area', self.throat.area)
        if self.mass_flow_rate:
            cs.add_variable('total_mass_flow_rate', self.mass_flow_rate)
        
        # Performance variables
        cs.add_variable('exit_velocity')
        cs.add_variable('thrust')
        cs.add_variable('specific_impulse')
        
        # Calculate performance if we have the required parameters
        if self.pressure and self.temperature and self.mass_flow_rate:
            # Constants for combustion products (LOX/LH2)
            gamma = cs.solved_values.get('gamma', 1.2)
            M = cs.solved_values.get('molecular_mass', 18)  # kg/kmol for combustion products
            Pe = cs.solved_values.get('exit_pressure', 101325)  # Pa
            
            # Compute exit velocity using isentropic nozzle flow
            R = 8314.5 / M
            Pc = self.pressure
            Tc = self.temperature
            pressure_ratio = Pe / Pc
            
            # Exit velocity calculation
            Ve = math.sqrt(2 * gamma * R * Tc / (gamma - 1) * 
                          (1 - pressure_ratio**((gamma - 1) / gamma)))
            cs.solved_values['exit_velocity'] = Ve
            
            # Thrust and specific impulse
            mdot = self.mass_flow_rate
            cs.solved_values['thrust'] = mdot * Ve
            cs.solved_values['specific_impulse'] = Ve / G0

@dataclass(slots=True)
class Nozzle(Component):
    expansion_ratio: Float = None
    exit_pressure: Float = None
    throat_area: Float = None
    exit_area: Float = None

    def add_constraints(self, cs: 'ConstraintSystem'):
        if self.exit_pressure:
            cs.add_variable('exit_pressure', self.exit_pressure)
        if self.expansion_ratio:
            cs.add_variable('expansion_ratio', self.expansion_ratio)

class ConstraintSystem:
    """Manages symbolic constraints and variable solving using sympy"""
    def __init__(self):
        self.variables: Dict[str, sp.Symbol] = {}
        self.constraints: List[Eq] = []
        self.solved_values: Dict[str, float] = {}

    def add_variable(self, name: str, value: Float = None):
        if name not in self.variables:
            sym = symbols(name)
            self.variables[name] = sym
        if value is not None:
            self.solved_values[name] = value

    def add_constraint(self, constraint: Eq):
        self.constraints.append(constraint)

    def solve_system(self) -> Dict[str, float]:
        """Solve the constraint system and return all solved values"""
        try:
            # Substitute known values
            subs = {self.variables[k]: v for k, v in self.solved_values.items() if k in self.variables}
            eqs = [c.subs(subs) for c in self.constraints]
            
            # Determine unknown symbols
            unk = set().union(*(e.free_symbols for e in eqs)) - set(subs.keys())
            if not unk:
                return self.solved_values

            # Solve for unknowns
            sol = solve(eqs, list(unk), dict=True)
            if sol:
                for sym, val in sol[0].items():
                    self.solved_values[str(sym)] = float(val)
        except Exception as e:
            print(f"Warning: Could not solve constraint system: {e}")
        
        return self.solved_values

@dataclass(slots=True)
class PropulsionSystem:
    components: Dict[str, Component] = field(default_factory=dict)
    constraint_system: ConstraintSystem = field(default_factory=ConstraintSystem)

    def __post_init__(self):
        self._setup()

    def _setup(self):
        """Setup constraint system with all component constraints"""
        cs = self.constraint_system
        
        # Register component-specific constraints
        for name, comp in self.components.items():
            # Add mass variables for all components
            if comp.mass:
                cs.add_variable(f"{name}_mass", comp.mass)
            
            # Let components add their own constraints
            if hasattr(comp, 'add_constraints'):
                comp.add_constraints(cs)

    def add_component(self, name: str, component: Component):
        """Add a component to the system"""
        self.components[name] = component
        self._setup()

    def solve(self) -> Dict[str, float]:
        """Solve the constraint system"""
        return self.constraint_system.solve_system()

    def thrust(self) -> float:
        """Get thrust in Newtons"""
        return self.solve().get('thrust', 0)

    def specific_impulse(self) -> float:
        """Get specific impulse in seconds"""
        return self.solve().get('specific_impulse', 0)

    def total_mass(self) -> float:
        """Calculate total system mass"""
        vals = self.solve()
        total = 0
        for name, comp in self.components.items():
            key = f"{name}_mass"
            if key in vals:
                total += vals[key]
            elif comp.mass:
                total += comp.mass
        return total

    def thrust_to_weight_ratio(self) -> float:
        """Calculate thrust-to-weight ratio"""
        return self.thrust() / (self.total_mass() * G0)

    def validate_constraints(self) -> Dict[str, bool]:
        """Validate key rocket constraints"""
        results = {}
        vals = self.solve()
        
        # Check if thrust meets target (25kN = 25000N)
        thrust = vals.get('thrust', 0)
        results['thrust_target'] = abs(thrust - 25000) < 1000  # Within 1kN
        
        # Check reasonable specific impulse (300-450s for chemical rockets)
        isp = vals.get('specific_impulse', 0)
        results['specific_impulse_range'] = 300 <= isp <= 450
        
        # Check thrust-to-weight ratio > 1 for rocket to lift off
        twr = self.thrust_to_weight_ratio()
        results['thrust_to_weight'] = twr > 1.0 if twr else False
        
        # Check chamber pressure is reasonable (1-20 MPa)
        pc = vals.get('chamber_pressure', 0)
        results['chamber_pressure_range'] = 1e6 <= pc <= 20e6
        
        # Check mass flow rate is reasonable
        mdot = vals.get('total_mass_flow_rate', 0)
        results['mass_flow_rate_positive'] = mdot > 0
        
        # Additional engineering constraints
        # Check O/F ratio is reasonable (4-8 for LOX/LH2)
        fuel_flow = 0
        ox_flow = 0
        for name, comp in self.components.items():
            if isinstance(comp, Pump):
                if 'fuel' in name:
                    fuel_flow = comp.mass_flow_rate or 0
                elif 'oxidizer' in name:
                    ox_flow = comp.mass_flow_rate or 0
        
        if fuel_flow > 0:
            of_ratio = ox_flow / fuel_flow
            results['of_ratio_reasonable'] = 4 <= of_ratio <= 8
        else:
            results['of_ratio_reasonable'] = False
            
        # Check pump pressure gains are adequate
        pressure_gain = vals.get('pump_pressure_gain', 0)
        tank_pressure = vals.get('tank_pressure', 0)
        chamber_pressure = vals.get('chamber_pressure', 0)
        if tank_pressure and chamber_pressure:
            results['pump_pressure_adequate'] = (tank_pressure + pressure_gain) > chamber_pressure
        else:
            results['pump_pressure_adequate'] = False
            
        # Check nozzle expansion ratio is reasonable (10-100)
        for name, comp in self.components.items():
            if isinstance(comp, Nozzle) and comp.expansion_ratio:
                results['expansion_ratio_reasonable'] = 10 <= comp.expansion_ratio <= 100
                break
        else:
            results['expansion_ratio_reasonable'] = False
        
        return results

    def print_summary(self):
        """Print a comprehensive summary of the rocket system"""
        vals = self.solve()
        constraints = self.validate_constraints()
        
        print("=== ROCKET SYSTEM SUMMARY ===")
        print(f"Target Thrust: 25,000 N")
        print(f"Actual Thrust: {vals.get('thrust', 0):.0f} N")
        print(f"Specific Impulse: {vals.get('specific_impulse', 0):.1f} s")
        print(f"Chamber Pressure: {vals.get('chamber_pressure', 0)/1e6:.1f} MPa")
        print(f"Mass Flow Rate: {vals.get('total_mass_flow_rate', 0):.2f} kg/s")
        print(f"Exit Velocity: {vals.get('exit_velocity', 0):.0f} m/s")
        print(f"Total Mass: {self.total_mass():.1f} kg")
        print(f"Thrust-to-Weight: {self.thrust_to_weight_ratio():.2f}")
        
        # Calculate O/F ratio properly
        fuel_flow = 0
        ox_flow = 0
        for name, comp in self.components.items():
            if isinstance(comp, Pump):
                if 'fuel' in name:
                    fuel_flow = comp.mass_flow_rate or 0
                elif 'oxidizer' in name:
                    ox_flow = comp.mass_flow_rate or 0
        
        if fuel_flow > 0:
            print(f"O/F Ratio: {ox_flow/fuel_flow:.1f}")
        
        # Pump power requirements
        for name, comp in self.components.items():
            if isinstance(comp, Pump):
                power_val = comp.power
                if power_val:
                    print(f"{name.title()} Power: {power_val/1000:.1f} kW")
        
        print("\n=== CONSTRAINT VALIDATION ===")
        passed = sum(1 for v in constraints.values() if v)
        total = len(constraints)
        print(f"Constraints Passed: {passed}/{total}")
        
        for constraint, passed in constraints.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {constraint.replace('_', ' ').title()}: {status}")
            
        return constraints


def create_25kn_rocket() -> PropulsionSystem:
    """Create a 25kN thrust rocket configuration using the elegant constraint system"""
    
    # Create fuel components
    oxidizer = LOX()
    fuel = LH2()
    
    # Create tanks
    fuel_tank = Tank(
        fuel=fuel,
        mass=40.0,  # kg
        volume=0.4,  # m^3
        pressure=2e6  # 2 MPa
    )
    
    oxidizer_tank = Tank(
        fuel=oxidizer,
        mass=60.0,  # kg
        volume=0.2,  # m^3
        pressure=2e6  # 2 MPa
    )
    
    # Create pumps with self-constraining design
    fuel_pump = Pump(
        mass=12.0,  # kg
        pressure_gain=8e6,  # 8 MPa boost
        efficiency=0.75,
        mass_flow_rate=1.2,  # kg/s (fine-tuned)
        fluid_density=fuel.density
    )
    
    oxidizer_pump = Pump(
        mass=15.0,  # kg
        pressure_gain=8e6,  # 8 MPa boost
        efficiency=0.75,
        mass_flow_rate=7.2,  # kg/s (fine-tuned, O/F ratio ~6:1)
        fluid_density=oxidizer.density
    )
    
    # Create injector
    injector = Injector(
        efficiency=0.95,
        pressure_loss=0.5e6,  # 0.5 MPa
        design_type="coaxial"
    )
    
    # Create throat
    throat = Throat(
        area=0.007  # m^2 (70 cm^2)
    )
    
    # Create combustion chamber with self-constraining performance calculation
    chamber = Chamber(
        injector=injector,
        pressure=10e6,  # 10 MPa
        throat=throat,
        temperature=3400,  # K
        mass_flow_rate=8.4,  # kg/s total (1.2 + 7.2)
        mass=80.0  # kg
    )
    
    # Create nozzle
    nozzle = Nozzle(
        expansion_ratio=25,  # Ae/At
        exit_pressure=101325,  # atmospheric
        throat_area=0.007,  # m^2
        exit_area=0.175,  # m^2 (25 * 0.007)
        mass=60.0  # kg
    )
    
    # Create propulsion system
    rocket = PropulsionSystem()
    
    # Add components - they will automatically add their own constraints
    rocket.add_component("fuel_tank", fuel_tank)
    rocket.add_component("oxidizer_tank", oxidizer_tank)
    rocket.add_component("fuel_pump", fuel_pump)
    rocket.add_component("oxidizer_pump", oxidizer_pump)
    rocket.add_component("chamber", chamber)
    rocket.add_component("nozzle", nozzle)
    
    return rocket


def demonstrate_constraints():
    chamber = Chamber(pressure=10e6, temperature=3400, mass_flow_rate=8.4, mass=80)
    cs = ConstraintSystem()
    cs.add_variable('exit_pressure', 101325)  # atmospheric
    
    print(f"   Before constraints: {len(cs.solved_values)} variables")
    chamber.add_constraints(cs)
    print(f"   After constraints:  {len(cs.solved_values)} variables")
    
    vals = cs.solve_system()
    print(f"   Auto-calculated thrust: {vals.get('thrust', 0):.0f} N")
    print(f"   Auto-calculated Isp:    {vals.get('specific_impulse', 0):.1f} s")
    


def create_test_suite():
    """Create a test suite to validate different rocket configurations"""
    print("=== ROCKET SYSTEM TEST SUITE ===\n")
    
    # Test 1: 25kN Rocket with elegant constraint system
    print("TEST 1: 25kN LOX/LH2 Rocket (Self-Constraining Design)")
    print("-" * 60)
    rocket_25k = create_25kn_rocket()
    constraints = rocket_25k.print_summary()
    
    # Test 2: Component constraint verification
    print("\n\nTEST 2: Constraint System Verification")
    print("-" * 45)
    vals = rocket_25k.solve()
    print("Key Performance Variables:")
    for key in ['thrust', 'specific_impulse', 'exit_velocity', 'chamber_pressure', 'total_mass_flow_rate']:
        if key in vals:
            print(f"  {key}: {vals[key]:.2f}")
    
    # Test 3: Elegant constraint demonstration
    print("\n\nTEST 3: Constraint System Demo")
    print("-" * 45)
    demonstrate_constraints()
    
    print("\n\nSUMMARY:")
    print(f"• Achieved {vals['thrust']:.0f}N thrust (target: 25,000N)")
    print(f"• Delivered {vals['specific_impulse']:.1f}s Isp (excellent performance)")
    print(f"• Validated {sum(constraints.values())}/{len(constraints)} engineering constraints")
    
    return rocket_25k


if __name__ == "__main__":
    create_test_suite()
