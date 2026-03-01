from enum import Enum


class FaseSimulacion(Enum):
    INICIO = "inicio"
    YENDO_A_PACIENTE = "yendo_a_paciente"
    EN_PACIENTE = "en_paciente"
    YENDO_A_HOSPITAL = "yendo_a_hospital"
    FIN = "fin"


class AppState:
    def __init__(self):
        self.fase: FaseSimulacion = FaseSimulacion.INICIO

        # Configuración inicial (introducida por el usuario)
        self.nombre_paciente: str = ""
        self.afeccion_paciente: str = ""

        # Nodo donde está el paciente (seleccionado de los 30 predefinidos)
        self.nodo_paciente: int = None

        # Ruta activa (lista de node_ids que la ambulancia debe recorrer)
        self.ruta_activa: list = []
        self.ruta_idx: int = 0

        # Hospital destino elegido (para fase 2)
        self.hospital_destino_node_id: int = None

        # Modo de ejecución
        self.modo_automatico: bool = False
        self.tick_interval_ms: int = 300

        # Referencia al modelo
        self.model = None

        # Callbacks para notificar a las ventanas
        self._listeners = []

    def registrar_listener(self, fn):
        self._listeners.append(fn)

    def notificar(self):
        for fn in self._listeners:
            try:
                fn()
            except Exception:
                pass

    def cambiar_fase(self, nueva_fase: FaseSimulacion):
        self.fase = nueva_fase
        self.notificar()
