import time
from Engine import Engine

def print_separator(title=""):
    """Helper para imprimir separadores bonitos"""
    print("\n" + "="*60)
    if title:
        print(f" {title}")
        print("="*60)

# Crear motor con dataset
print("Inicializando motor...")
engine = Engine('datasetMotor\engine_failure_dataset.csv')

# Arrancar motor
engine.start()

# Test 1: Operación IDLE normal
print_separator("TEST 1: MODO IDLE - OPERACIÓN NORMAL")
for i in range(5):
    engine.tick()
    telemetry = engine.get_telemetry()
    health = engine.check_health()
    print(f"Tick {i+1}: Temp={telemetry['temperature']:6.1f}°C | "
          f"RPM={telemetry['rpm']:7.0f} | "
          f"Fuel={telemetry['fuel_efficiency']:5.1f} | "
          f"Vib={telemetry['vibration_magnitude']:.3f} | "
          f"Health={health['health_score']:5.1f}%")
    time.sleep(0.3)

# Test 2: Cambiar a CRUISING
print_separator("TEST 2: CAMBIO A MODO CRUISING")
engine.set_operational_mode(Engine.MODE_CRUISING)
for i in range(5):
    engine.tick()
    telemetry = engine.get_telemetry()
    health = engine.check_health()
    print(f"Tick {i+1}: Temp={telemetry['temperature']:6.1f}°C | "
          f"RPM={telemetry['rpm']:7.0f} | "
          f"Fuel={telemetry['fuel_efficiency']:5.1f} | "
          f"Health={health['health_score']:5.1f}%")
    time.sleep(0.3)

# Test 3: Cambiar a HEAVY LOAD
print_separator("TEST 3: CAMBIO A MODO HEAVY LOAD")
engine.set_operational_mode(Engine.MODE_HEAVY_LOAD)
for i in range(5):
    engine.tick()
    telemetry = engine.get_telemetry()
    health = engine.check_health()
    print(f"Tick {i+1}: Temp={telemetry['temperature']:6.1f}°C | "
          f"RPM={telemetry['rpm']:7.0f} | "
          f"Health={health['health_score']:5.1f}%")
    time.sleep(0.3)

# Test 4: Inyectar fallo LEVE
print_separator("TEST 4: FALLO LEVE (factor=1.3)")
engine.inject_fault(1.3)
for i in range(5):
    engine.tick()
    telemetry = engine.get_telemetry()
    health = engine.check_health()
    print(f"Tick {i+1}: Temp={telemetry['temperature']:6.1f}°C | "
          f"Vib={telemetry['vibration_magnitude']:.3f} | "
          f"Fuel={telemetry['fuel_efficiency']:5.1f} | "
          f"Health={health['health_score']:5.1f}% | "
          f"Issues: {', '.join(health['issues']) if health['issues'] else 'None'}")
    time.sleep(0.3)

# Test 5: Inyectar fallo SEVERO
print_separator("TEST 5: FALLO SEVERO (factor=2.0)")
engine.inject_fault(2.0)
for i in range(5):
    engine.tick()
    telemetry = engine.get_telemetry()
    health = engine.check_health()
    print(f"🚨 Tick {i+1}: Temp={telemetry['temperature']:6.1f}°C | "
          f"Vib={telemetry['vibration_magnitude']:.3f} | "
          f"Health={health['health_score']:5.1f}% | "
          f"Severity={health['severity']}")
    time.sleep(0.3)

# Test 6: Volver a normal
print_separator("TEST 6: RECUPERACIÓN - VOLVER A NORMAL")
engine.inject_fault(1.0)
for i in range(5):
    engine.tick()
    telemetry = engine.get_telemetry()
    health = engine.check_health()
    print(f"Tick {i+1}: Temp={telemetry['temperature']:6.1f}°C | "
          f"Health={health['health_score']:5.1f}% | "
          f"Severity={health['severity']}")
    time.sleep(0.3)

# Detener motor
print_separator()
engine.stop()

# Mostrar telemetría completa final
print_separator("TELEMETRÍA COMPLETA")
print(engine.get_telemetry())