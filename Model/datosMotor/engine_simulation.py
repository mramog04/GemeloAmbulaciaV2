import pandas as pd
import numpy as np
from typing import Optional, Dict
from dataclasses import dataclass

@dataclass
class ModeStats:
    """Estadísticas (media y desviación estándar) para un modo operacional"""
    temp_mean: float
    temp_std: float
    rpm_mean: float
    rpm_std: float
    fuel_eff_mean: float
    fuel_eff_std: float
    vib_x_mean: float
    vib_x_std: float
    vib_y_mean: float
    vib_y_std: float
    vib_z_mean: float
    vib_z_std: float
    torque_mean: float
    torque_std: float
    power_mean: float
    power_std: float


class Engine:
    """Motor de ambulancia con simulación basada en dataset"""
    
    # Modos operacionales
    MODE_IDLE = "Idle"
    MODE_CRUISING = "Cruising"
    MODE_HEAVY_LOAD = "Heavy Load"
    
    def __init__(self, dataset_path: str):
        """
        Inicializa el motor cargando estadísticas del dataset.
        
        Args:
            dataset_path: Ruta al archivo CSV con datos históricos
        """
        self.is_running = False
        self.operational_mode = self.MODE_IDLE
        self.failure_factor = 1.0
        
        # Estado actual del motor
        self.Temperature = 0.0
        self.RPM = 0.0
        self.Fuel_efficiency = 0.0
        self.Vibration_X = 0.0
        self.Vibration_Y = 0.0
        self.Vibration_Z = 0.0
        self.Torque = 0.0
        self.Power_Output = 0.0
        
        # Cargar estadísticas del dataset
        self.stats: Dict[str, ModeStats] = {}
        self._load_stats_from_dataset(dataset_path)
    
    def _load_stats_from_dataset(self, dataset_path: str):
        """Calcula estadísticas (μ, σ) por modo operacional desde el dataset"""
        try:
            df = pd.read_csv(dataset_path)
            
            # Mapeo de nombres de columnas (por si tienen espacios o paréntesis)
            column_mapping = {
                'Temperature (°C)': 'Temperature',
                'Power_Output (kW)': 'Power_Output'
            }
            df.rename(columns=column_mapping, inplace=True, errors='ignore')
            
            # Calcular estadísticas para cada modo operacional
            for mode in df['Operational_Mode'].unique():
                mode_data = df[df['Operational_Mode'] == mode]
                
                self.stats[mode] = ModeStats(
                    temp_mean=mode_data['Temperature'].mean(),
                    temp_std=mode_data['Temperature'].std(),
                    rpm_mean=mode_data['RPM'].mean(),
                    rpm_std=mode_data['RPM'].std(),
                    fuel_eff_mean=mode_data['Fuel_Efficiency'].mean(),
                    fuel_eff_std=mode_data['Fuel_Efficiency'].std(),
                    vib_x_mean=mode_data['Vibration_X'].mean(),
                    vib_x_std=mode_data['Vibration_X'].std(),
                    vib_y_mean=mode_data['Vibration_Y'].mean(),
                    vib_y_std=mode_data['Vibration_Y'].std(),
                    vib_z_mean=mode_data['Vibration_Z'].mean(),
                    vib_z_std=mode_data['Vibration_Z'].std(),
                    torque_mean=mode_data['Torque'].mean(),
                    torque_std=mode_data['Torque'].std(),
                    power_mean=mode_data['Power_Output'].mean(),
                    power_std=mode_data['Power_Output'].std()
                )
            
            print(f"✅ Estadísticas cargadas para {len(self.stats)} modos operacionales:")
            for mode, stats in self.stats.items():
                print(f"   - {mode}: Temp={stats.temp_mean:.1f}°C (±{stats.temp_std:.1f}), "
                      f"RPM={stats.rpm_mean:.0f} (±{stats.rpm_std:.0f})")
        
        except Exception as e:
            print(f"❌ Error cargando dataset: {e}")
            raise
    
    def start(self):
        """Arranca el motor en modo IDLE"""
        if not self.is_running:
            self.is_running = True
            self.operational_mode = self.MODE_IDLE
            self.update_idle()
            print("🚀 Motor arrancado en modo IDLE")
    
    def stop(self):
        """Detiene el motor y resetea valores"""
        self.is_running = False
        self.Temperature = 0.0
        self.RPM = 0.0
        self.Fuel_efficiency = 0.0
        self.Vibration_X = 0.0
        self.Vibration_Y = 0.0
        self.Vibration_Z = 0.0
        self.Torque = 0.0
        self.Power_Output = 0.0
        print("🛑 Motor detenido")
    
    def set_operational_mode(self, mode: str):
        """
        Cambia el modo operacional del motor.
        
        Args:
            mode: Uno de MODE_IDLE, MODE_CRUISING, MODE_HEAVY_LOAD
        """
        if not self.is_running:
            print("⚠️  El motor debe estar arrancado primero")
            return
        
        if mode not in self.stats:
            print(f"❌ Modo '{mode}' no encontrado en el dataset")
            print(f"   Modos disponibles: {list(self.stats.keys())}")
            return
        
        self.operational_mode = mode
        print(f"🔧 Modo cambiado a: {mode}")
        
        # Actualizar valores según el nuevo modo
        if mode == self.MODE_IDLE:
            self.update_idle(self.failure_factor)
        elif mode == self.MODE_CRUISING:
            self.update_cruising(self.failure_factor)
        elif mode == self.MODE_HEAVY_LOAD:
            self.update_heavy_load(self.failure_factor)
    
    def inject_fault(self, failure_factor: float = 1.0):
        """
        Inyecta un fallo en el motor modificando el factor de degradación.
        
        Args:
            failure_factor: Factor multiplicador
                - 1.0: operación normal
                - 1.2: fallo leve (+20% degradación)
                - 1.5: fallo moderado (+50% degradación)
                - 2.0: fallo severo (+100% degradación)
        """
        self.failure_factor = failure_factor
        
        if failure_factor == 1.0:
            print("✅ Sistema operando normalmente")
        elif failure_factor <= 1.3:
            print(f"⚠️  Fallo LEVE inyectado (factor={failure_factor})")
        elif failure_factor <= 1.7:
            print(f"⚠️⚠️  Fallo MODERADO inyectado (factor={failure_factor})")
        else:
            print(f"🚨🚨 Fallo SEVERO inyectado (factor={failure_factor})")
        
        # Actualizar telemetría con el nuevo factor
        self.tick()
    
    def update_idle(self, failure_factor: float = 1.0):
        """
        Actualiza telemetría en modo IDLE.
        
        Args:
            failure_factor: Factor de multiplicación para simular fallos
        """
        if self.MODE_IDLE not in self.stats:
            print(f"⚠️  No hay estadísticas para modo IDLE")
            return
        
        stats = self.stats[self.MODE_IDLE]
        
        # Variables que AUMENTAN con fallos
        temp_base = np.random.normal(stats.temp_mean, stats.temp_std)
        self.Temperature = np.clip(temp_base * failure_factor, 0, 150)
        
        vib_x_base = np.random.normal(stats.vib_x_mean, stats.vib_x_std)
        self.Vibration_X = vib_x_base * failure_factor
        
        vib_y_base = np.random.normal(stats.vib_y_mean, stats.vib_y_std)
        self.Vibration_Y = vib_y_base * failure_factor
        
        vib_z_base = np.random.normal(stats.vib_z_mean, stats.vib_z_std)
        self.Vibration_Z = vib_z_base * failure_factor
        
        # Variables que DISMINUYEN con fallos
        fuel_base = np.random.normal(stats.fuel_eff_mean, stats.fuel_eff_std)
        self.Fuel_efficiency = max(0, fuel_base / failure_factor)
        
        power_base = np.random.normal(stats.power_mean, stats.power_std)
        self.Power_Output = max(0, power_base / failure_factor)
        
        # Variables NO afectadas por fallos
        self.RPM = max(0, np.random.normal(stats.rpm_mean, stats.rpm_std))
        self.Torque = max(0, np.random.normal(stats.torque_mean, stats.torque_std))
    
    def update_cruising(self, failure_factor: float = 1.0):
        """
        Actualiza telemetría en modo CRUISING.
        
        Args:
            failure_factor: Factor de multiplicación para simular fallos
        """
        if self.MODE_CRUISING not in self.stats:
            print(f"⚠️  No hay estadísticas para modo CRUISING")
            return
        
        stats = self.stats[self.MODE_CRUISING]
        
        # Variables que AUMENTAN con fallos
        temp_base = np.random.normal(stats.temp_mean, stats.temp_std)
        self.Temperature = np.clip(temp_base * failure_factor, 0, 150)
        
        vib_x_base = np.random.normal(stats.vib_x_mean, stats.vib_x_std)
        self.Vibration_X = vib_x_base * failure_factor
        
        vib_y_base = np.random.normal(stats.vib_y_mean, stats.vib_y_std)
        self.Vibration_Y = vib_y_base * failure_factor
        
        vib_z_base = np.random.normal(stats.vib_z_mean, stats.vib_z_std)
        self.Vibration_Z = vib_z_base * failure_factor
        
        # Variables que DISMINUYEN con fallos
        fuel_base = np.random.normal(stats.fuel_eff_mean, stats.fuel_eff_std)
        self.Fuel_efficiency = max(0, fuel_base / failure_factor)
        
        power_base = np.random.normal(stats.power_mean, stats.power_std)
        self.Power_Output = max(0, power_base / failure_factor)
        
        # Variables NO afectadas por fallos
        self.RPM = max(0, np.random.normal(stats.rpm_mean, stats.rpm_std))
        self.Torque = max(0, np.random.normal(stats.torque_mean, stats.torque_std))
    
    def update_heavy_load(self, failure_factor: float = 1.0):
        """
        Actualiza telemetría en modo HEAVY LOAD.
        
        Args:
            failure_factor: Factor de multiplicación para simular fallos
        """
        if self.MODE_HEAVY_LOAD not in self.stats:
            print(f"⚠️  No hay estadísticas para modo HEAVY LOAD")
            return
        
        stats = self.stats[self.MODE_HEAVY_LOAD]
        
        # Variables que AUMENTAN con fallos
        temp_base = np.random.normal(stats.temp_mean, stats.temp_std)
        self.Temperature = np.clip(temp_base * failure_factor, 0, 150)
        
        vib_x_base = np.random.normal(stats.vib_x_mean, stats.vib_x_std)
        self.Vibration_X = vib_x_base * failure_factor
        
        vib_y_base = np.random.normal(stats.vib_y_mean, stats.vib_y_std)
        self.Vibration_Y = vib_y_base * failure_factor
        
        vib_z_base = np.random.normal(stats.vib_z_mean, stats.vib_z_std)
        self.Vibration_Z = vib_z_base * failure_factor
        
        # Variables que DISMINUYEN con fallos
        fuel_base = np.random.normal(stats.fuel_eff_mean, stats.fuel_eff_std)
        self.Fuel_efficiency = max(0, fuel_base / failure_factor)
        
        power_base = np.random.normal(stats.power_mean, stats.power_std)
        self.Power_Output = max(0, power_base / failure_factor)
        
        # Variables NO afectadas por fallos
        self.RPM = max(0, np.random.normal(stats.rpm_mean, stats.rpm_std))
        self.Torque = max(0, np.random.normal(stats.torque_mean, stats.torque_std))
    
    def tick(self):
        """Actualiza el estado del motor (llamar cada ciclo de simulación)"""
        if not self.is_running:
            return
        
        # Llamar a la función de actualización según el modo actual
        if self.operational_mode == self.MODE_IDLE:
            self.update_idle(self.failure_factor)
        elif self.operational_mode == self.MODE_CRUISING:
            self.update_cruising(self.failure_factor)
        elif self.operational_mode == self.MODE_HEAVY_LOAD:
            self.update_heavy_load(self.failure_factor)
    
    def get_telemetry(self) -> dict:
        """Retorna el estado actual del motor como diccionario"""
        return {
            'is_running': self.is_running,
            'operational_mode': self.operational_mode,
            'failure_factor': self.failure_factor,
            'temperature': round(self.Temperature, 2),
            'rpm': round(self.RPM, 2),
            'fuel_efficiency': round(self.Fuel_efficiency, 2),
            'vibration_x': round(self.Vibration_X, 4),
            'vibration_y': round(self.Vibration_Y, 4),
            'vibration_z': round(self.Vibration_Z, 4),
            'torque': round(self.Torque, 2),
            'power_output': round(self.Power_Output, 2),
            'vibration_magnitude': round(self._get_vibration_magnitude(), 4)
        }
    
    def _get_vibration_magnitude(self) -> float:
        """Calcula la magnitud total de vibración"""
        return np.sqrt(self.Vibration_X**2 + self.Vibration_Y**2 + self.Vibration_Z**2)
    
    def check_health(self) -> dict:
        """Evalúa el estado de salud del motor"""
        issues = []
        severity = "NORMAL"
        
        if self.Temperature > 100:
            issues.append("Temperatura crítica")
            severity = "CRITICAL"
        elif self.Temperature > 90:
            issues.append("Temperatura elevada")
            severity = "WARNING" if severity == "NORMAL" else severity
        
        if self.RPM > 4000:
            issues.append("RPM excesivas")
            severity = "WARNING" if severity == "NORMAL" else severity
        
        vib_mag = self._get_vibration_magnitude()
        if vib_mag > 1.5:
            issues.append("Vibración anormal")
            severity = "CRITICAL"
        elif vib_mag > 1.0:
            issues.append("Vibración elevada")
            severity = "WARNING" if severity == "NORMAL" else severity
        
        if self.Fuel_efficiency < 15:
            issues.append("Eficiencia de combustible baja")
            severity = "WARNING" if severity == "NORMAL" else severity
        
        return {
            'severity': severity,
            'issues': issues,
            'health_score': self._calculate_health_score()
        }
    
    def _calculate_health_score(self) -> float:
        """Calcula un score de salud del 0 al 100"""
        score = 100.0
        
        # Penalizar por temperatura alta
        if self.Temperature > 90:
            score -= min((self.Temperature - 90) * 2, 30)
        
        # Penalizar por vibración
        vib_mag = self._get_vibration_magnitude()
        if vib_mag > 1.0:
            score -= min((vib_mag - 1.0) * 30, 30)
        
        # Penalizar por eficiencia baja
        if self.Fuel_efficiency < 20:
            score -= min((20 - self.Fuel_efficiency) * 2, 20)
        
        # Penalizar por factor de fallo
        score -= (self.failure_factor - 1.0) * 20
        
        return max(0, round(score, 1))
    
    def __repr__(self):
        return (f"Engine(running={self.is_running}, mode={self.operational_mode}, "
                f"temp={self.Temperature:.1f}°C, rpm={self.RPM:.0f}, "
                f"failure_factor={self.failure_factor})")