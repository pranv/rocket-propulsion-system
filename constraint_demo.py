#!/usr/bin/env python3
"""
Demonstration of the constraint-based rocket system analysis.

This shows how the system can solve for missing values given different 
sets of known parameters.
"""

from rocket_system import *

# Create fuel definition
lh2 = Fuel(
    name="LH2",
    density=70.8,
    specific_heat=14300,
    initial_temperature=20,
    boiling_point=20.28,
    combustion_temperature=3500,
    molecular_mass=2.016,
)

def create_engine():
    """Create a standard engine configuration."""
    return EngineConfig(
        fuel=lh2,
        oxidizer=lh2,  # Using same for simplicity
        tank=Tank(pressure=2e6, max_volume=1.5, insulation_rating=0.9),
        pump=Pump(pressure_gain=10e6, efficiency=0.6, min_torque=500),
        chamber=Chamber(
            injector=Injector(pressure_loss=1.5e6, design_type="pintle"),
            regen_cooling_loss=0.5e6,
            expander_loss=0.0,
            plumbing_losses=0.2e6,
            min_pressure=8e6,
        ),
        nozzle=Nozzle(exit_pressure=0.1e6, expansion_ratio=16),
        throat=Throat(area=0.01),
    )

def demo_forward_analysis():
    """Standard forward analysis: given design parameters, find performance."""
    print("=== Forward Analysis ===")
    print("Given: tank pressure, pump gain, losses, nozzle exit pressure")
    print("Find: chamber pressure, exit velocity, ISP, thrust")
    
    engine = create_engine()
    engine.values["mass_flow_rate"] = 3.0  # kg/s
    
    # The constraint system automatically solves the dependency chain
    results = engine.solve_constraints()
    
    print(f"Chamber pressure: {engine.values['chamber_pressure']:.0f} Pa")
    print(f"Exit velocity: {engine.values['exit_velocity']:.1f} m/s")
    print(f"Specific impulse: {engine.values['isp']:.1f} s")
    print(f"Thrust: {engine.values['thrust']:.1f} N")
    print()

def demo_what_if_analysis():
    """What-if analysis: change one parameter and see effects."""
    print("=== What-If Analysis ===")
    print("Effect of changing pump pressure gain:")
    
    base_engine = create_engine()
    base_engine.values["mass_flow_rate"] = 3.0
    
    pump_gains = [8e6, 10e6, 12e6, 15e6]  # Pa
    
    for gain in pump_gains:
        engine = create_engine()
        engine.pump.pressure_gain = gain
        engine.values["mass_flow_rate"] = 3.0
        
        # Redefine constraints with new pump gain
        engine.cycles[0].define_constraints(engine.fuel)
        
        results = engine.solve_constraints()
        
        isp = engine.values['isp']
        thrust = engine.values['thrust']
        
        print(f"  Pump gain: {gain/1e6:.0f} MPa -> ISP: {isp:.1f} s, Thrust: {thrust:.1f} N")
    print()

def demo_reverse_engineering():
    """Reverse engineering: given desired performance, find required parameters."""
    print("=== Reverse Engineering Example ===")
    print("If we want 1000 s ISP, what exit velocity do we need?")
    
    # Create a simple constraint system manually
    target_isp = 1000  # s
    required_ve = target_isp * G0
    
    print(f"Required exit velocity: {required_ve:.1f} m/s")
    
    # Now let's see what chamber pressure we'd need
    engine = create_engine()
    nozzle = engine.nozzle
    Pe = nozzle.exit_pressure
    gamma = 1.22
    R = lh2.R()
    Tc = lh2.combustion_temperature
    
    # Solve the rocket equation backwards for chamber pressure
    # Ve = sqrt(2*gamma*R*Tc/(gamma-1) * (1 - (Pe/Pc)^((gamma-1)/gamma)))
    # This is a transcendental equation, so we'll use numerical methods
    
    import scipy.optimize as opt
    
    def rocket_equation(pc):
        pr = Pe / pc
        term = (2 * gamma * R * Tc) / (gamma - 1)
        vel_term = 1 - pr ** ((gamma - 1) / gamma)
        return math.sqrt(term * vel_term) - required_ve
    
    # Find the chamber pressure that gives us the desired exit velocity
    try:
        pc_required = opt.fsolve(rocket_equation, 15e6)[0]  # Initial guess 15 MPa
        print(f"Required chamber pressure: {pc_required/1e6:.1f} MPa")
        
        # What pump gain would we need?
        engine = create_engine()
        losses = sum(x or 0 for x in [
            engine.chamber.plumbing_losses,
            engine.chamber.regen_cooling_loss,
            engine.chamber.expander_loss,
            engine.chamber.injector.pressure_loss,
        ])
        
        required_pump_gain = pc_required - engine.tank.pressure + losses
        print(f"Required pump gain: {required_pump_gain/1e6:.1f} MPa")
        print(f"(Current pump gain: {engine.pump.pressure_gain/1e6:.1f} MPa)")
        
    except:
        print("Could not solve for required chamber pressure")
    
    print()

def demo_constraint_flexibility():
    """Show how the constraint system handles different scenarios."""
    print("=== Constraint System Flexibility ===")
    
    # Scenario 1: All parameters known
    print("1. All parameters specified:")
    engine = create_engine()
    engine.values.update({
        "mass_flow_rate": 3.0,
        "chamber_pressure": 9.8e6,
        "exit_velocity": 9490,
    })
    
    results = engine.solve_constraints()
    print(f"   ISP: {engine.values['isp']:.1f} s")
    print(f"   Thrust: {engine.values['thrust']:.1f} N")
    
    # Scenario 2: Only some parameters known
    print("\n2. Only mass flow rate and chamber pressure known:")
    engine2 = create_engine()
    engine2.values.update({
        "mass_flow_rate": 2.5,
        "chamber_pressure": 12e6,
    })
    
    # Override chamber pressure (as if measured)
    fuel_cycle = engine2.cycles[0]
    fuel_cycle.variables['P_chamber'] = 12e6
    
    results2 = engine2.solve_constraints()
    print(f"   Exit velocity: {engine2.values['exit_velocity']:.1f} m/s")
    print(f"   ISP: {engine2.values['isp']:.1f} s")
    print(f"   Thrust: {engine2.values['thrust']:.1f} N")

if __name__ == "__main__":
    demo_forward_analysis()
    demo_what_if_analysis()
    demo_reverse_engineering()
    demo_constraint_flexibility() 