import numpy as np
import random

GRAVEDADES = ["leve", "media", "grave"]
NOMBRES_EJEMPLO = [
    "Carlos Sánchez", "Manuela López", "Luis García", "Isabel Torres", "Daniel Martín",
    "Carmen Pérez", "Juan Ortega", "Beatriz Ruiz", "Pedro Ramos", "Ana Fernández"
]

class PacienteSimulado:
    """
    Simulador sencillo de constantes vitales de un paciente, categorizados por gravedad.
    """
    def __init__(self, gravedad=None):
        # Selecciona gravedad aleatoria si no la dan
        self.gravedad = gravedad if gravedad in GRAVEDADES else random.choice(GRAVEDADES)
        self.nombre = random.choice(NOMBRES_EJEMPLO)

        # Al inicializar, genera valores realistas según gravedad
        self.fc = self._simular_fc()
        self.pa_sis, self.pa_dia = self._simular_pa()
        self.spo2 = self._simular_spo2()
        self.fr = self._simular_fr()

    def _simular_fc(self):
        if self.gravedad == "leve":
            return int(np.random.normal(80, 10))  # 60–100
        elif self.gravedad == "media":
            return int(np.random.normal(115, 10))  # 100–130
        else:
            return int(np.random.normal(155, 15))  # 130–180

    def _simular_pa(self):
        if self.gravedad == "leve":
            return (int(np.random.normal(125, 10)), int(np.random.normal(80, 8)))  # 110–140/70–90
        elif self.gravedad == "media":
            return (int(np.random.normal(100, 8)), int(np.random.normal(70, 8)))   # 90–110/60–80
        else:
            return (int(np.random.normal(75, 8)), int(np.random.normal(50, 8)))    # 60–90/40–60

    def _simular_spo2(self):
        if self.gravedad == "leve":
            return round(np.random.normal(98, 1.5), 1)   # 96–100
        elif self.gravedad == "media":
            return round(np.random.normal(94, 1.5), 1)   # 92–96
        else:
            return round(np.random.normal(89, 2), 1)     # 85–92

    def _simular_fr(self):
        if self.gravedad == "leve":
            return int(np.random.normal(16, 2))          # 12–20
        elif self.gravedad == "media":
            return int(np.random.normal(24, 2))          # 21–28
        else:
            return int(np.random.normal(34, 3))          # 29–40

    def actualizar_estado(self, probabilidad_agravamiento: float = 0.1):
        """
        Actualiza las constantes vitales del paciente.
        Con probabilidad probabilidad_agravamiento, la gravedad aumenta un nivel.
        Si ya es 'grave', solo se regeneran los valores actuales.
        """
        incrementar = random.random() < probabilidad_agravamiento
        if self.gravedad != "grave" and incrementar:
            idx = GRAVEDADES.index(self.gravedad)
            self.gravedad = GRAVEDADES[idx + 1]
            # Opcional: Mensaje de agravamiento
            # print(f"¡El paciente ha empeorado a gravedad '{self.gravedad}'!")
        # Regenerar valores según la (posible nueva) gravedad
        self.fc = self._simular_fc()
        self.pa_sis, self.pa_dia = self._simular_pa()
        self.spo2 = self._simular_spo2()
        self.fr = self._simular_fr()

    def get_telemetria(self):
        return {
            "nombre": self.nombre,
            "gravedad": self.gravedad,
            "fc": self.fc,
            "pa_sistolica": self.pa_sis,
            "pa_diastolica": self.pa_dia,
            "spo2": self.spo2,
            "fr": self.fr,
        }

    def __repr__(self):
        return f"Paciente {self.nombre} | Gravedad: {self.gravedad} | FC: {self.fc} | PA: {self.pa_sis}/{self.pa_dia} | SpO2: {self.spo2}% | FR: {self.fr}"