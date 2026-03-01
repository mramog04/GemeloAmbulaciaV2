import csv
import os
from datetime import datetime
from typing import Optional


class PersistenciaLayer:
    """
    Capa de Persistencia del Gemelo Digital.

    Guarda en un archivo CSV un snapshot del estado físico de la ambulancia
    en cada tick de simulación. Genera un historial trazable que permite
    análisis de rendimiento y soporte a predicciones a largo plazo.

    El archivo CSV se crea automáticamente en el directorio indicado.
    Cada fila corresponde a un tick, con timestamp y todas las métricas
    aplanadas del snapshot (motor, paciente, posición).
    """

    # Columnas fijas del CSV (orden garantizado)
    COLUMNAS = [
        'timestamp',
        'tick',
        'node_id',
        'lat',
        'lon',
        'velocidad_kmh',
        'rumbo',
        # Motor
        'engine_temperature',
        'engine_rpm',
        'engine_oil_pressure',
        'engine_fuel_efficiency',
        'engine_vibration',
        'engine_health_score',
        # Paciente
        'paciente_fc',
        'paciente_spo2',
        'paciente_frecuencia_resp',
        'paciente_presion_sistolica',
        'paciente_presion_diastolica',
    ]

    def __init__(self, ruta_csv: str = 'datos_persistencia/snapshots.csv'):
        """
        Inicializa la capa de persistencia.

        Args:
            ruta_csv: Ruta del fichero CSV donde se guardarán los snapshots.
        """
        self._ruta_csv = ruta_csv
        self._tick_count: int = 0

        # Crear directorio si no existe
        directorio = os.path.dirname(ruta_csv)
        if directorio:
            os.makedirs(directorio, exist_ok=True)

        # Escribir cabecera si el fichero no existe
        if not os.path.exists(ruta_csv):
            with open(ruta_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.COLUMNAS)
                writer.writeheader()

    def guardar_snapshot(self, snapshot: dict):
        """
        Aplana el snapshot del estado físico y lo guarda como fila en el CSV.

        Args:
            snapshot: Dict devuelto por fisical_ambulance.snapshot() con claves
                      'engine', 'paciente' y 'posicion'.
        """
        engine = snapshot.get('engine') or {}
        paciente = snapshot.get('paciente') or {}
        posicion = snapshot.get('posicion') or {}

        presion = paciente.get('presion_arterial') or {}
        coordenadas = posicion.get('coordenadas') or (None, None)
        lat, lon = coordenadas

        fila = {
            'timestamp': datetime.now().isoformat(),
            'tick': self._tick_count,
            'node_id': posicion.get('node_id', ''),
            'lat': lat if lat is not None else '',
            'lon': lon if lon is not None else '',
            'velocidad_kmh': posicion.get('velocidad', ''),
            'rumbo': posicion.get('rumbo', ''),
            'engine_temperature': engine.get('temperature', ''),
            'engine_rpm': engine.get('rpm', ''),
            'engine_oil_pressure': engine.get('oil_pressure', ''),
            'engine_fuel_efficiency': engine.get('fuel_efficiency', ''),
            'engine_vibration': engine.get('vibration_magnitude', ''),
            'engine_health_score': engine.get('health_score', ''),
            'paciente_fc': paciente.get('fc', ''),
            'paciente_spo2': paciente.get('spo2', ''),
            'paciente_frecuencia_resp': paciente.get('frecuencia_resp', ''),
            'paciente_presion_sistolica': presion.get('sistolica', ''),
            'paciente_presion_diastolica': presion.get('diastolica', ''),
        }

        # Sustituir None por ''
        fila = {k: ('' if v is None else v) for k, v in fila.items()}

        with open(self._ruta_csv, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.COLUMNAS)
            writer.writerow(fila)

        self._tick_count += 1

    def get_ruta_csv(self) -> str:
        """Devuelve la ruta del fichero CSV."""
        return self._ruta_csv

    def get_total_ticks(self) -> int:
        """Devuelve el número de ticks guardados."""
        return self._tick_count

    def reset(self):
        """
        Renombra el CSV actual con timestamp y crea uno nuevo vacío con cabecera.
        Útil para empezar un nuevo viaje.
        """
        if os.path.exists(self._ruta_csv):
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            directorio = os.path.dirname(self._ruta_csv)
            nombre_base = os.path.splitext(os.path.basename(self._ruta_csv))[0]
            nueva_ruta = os.path.join(directorio, f"{nombre_base}_{ts}.csv")
            os.rename(self._ruta_csv, nueva_ruta)

        self._tick_count = 0

        with open(self._ruta_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.COLUMNAS)
            writer.writeheader()
