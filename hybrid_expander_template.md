
# 🚀 Hybrid Expander-Electric Rocket Engine Design Template

Use this Markdown file to run calculations in a code-friendly environment (e.g. Jupyter Notebook, VS Code).

---

## ✳️ Step 1: Define Mission Parameters

```python
# Constants
g0 = 9.81  # m/s^2

# Engine specs
T = 50_000  # Thrust in Newtons
Isp = 350   # Specific impulse in seconds
burn_time = 60  # seconds
OF_ratio = 3.5  # Oxidizer/Fuel ratio

# Propellant properties
rho_fuel = 422     # kg/m^3 (Methane)
rho_ox = 1141      # kg/m^3 (LOX)
cp_fuel = 2600     # J/kg.K (approx for gaseous methane)

# Pump and turbine efficiencies
eta_p = 0.7
eta_turb = 0.7
eta_motor = 0.9
eta_gen = 0.9
```

---

## 🚰 Step 2: Propellant Flow Rates

```python
mdot_total = T / (g0 * Isp)
mdot_fuel = mdot_total / (1 + OF_ratio)
mdot_ox = mdot_total - mdot_fuel
```

---

## ⚙️ Step 3: Pump Power Requirements

```python
delta_P = 68e5  # Pa, from ~2 bar tank to ~70 bar chamber

P_fuel_pump = (mdot_fuel * delta_P) / (rho_fuel * eta_p)
P_ox_pump = (mdot_ox * delta_P) / (rho_ox * eta_p)
P_pump_total = P_fuel_pump + P_ox_pump
```

---

## 🔥 Step 4: Turbine Power Available

```python
T_inlet = 300  # K
T_exit = 800   # K

P_turbine_in = mdot_fuel * cp_fuel * (T_exit - T_inlet)
P_turbine_out = eta_turb * P_turbine_in
```

---

## ⚡ Step 5: Electric System Sizing

```python
# Account for conversion losses
P_required_elec = P_pump_total / (eta_motor * eta_gen)

# Startup battery sizing
startup_time = 10  # seconds
E_battery = P_required_elec * startup_time  # in Joules

# Battery mass
battery_specific_energy = 720e3  # J/kg (200 Wh/kg)
m_battery = E_battery / battery_specific_energy
```

---

## ⚖️ Step 6: Mass Estimates (Custom Inputs)

```python
motor_specific_power = 3.0  # kW/kg
gen_specific_power = 5.0    # kW/kg

motor_mass = P_pump_total / (motor_specific_power * 1e3)
generator_mass = P_required_elec / (gen_specific_power * 1e3)
```

---

## ✅ Step 7: Evaluation

Compare:
- Turbine power vs. required pump power
- Battery/motor/generator mass vs. benefits (startup, throttling, redundancy)

---
