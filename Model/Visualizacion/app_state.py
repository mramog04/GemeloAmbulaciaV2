from enum import Enum


class FaseSimulacion(Enum):
    INICIO = "inicio"
    YENDO_A_PACIENTE = "yendo_a_paciente"
    EN_PACIENTE = "en_paciente"
    YENDO_A_HOSPITAL = "yendo_a_hospital"
    FIN = "fin"


class AppState:
    def __init__(self):
        self.fase = FaseSimulacion.INICIO
        self.nombre_paciente = ""
        self.afeccion_paciente = ""
        self.nodo_paciente = None          # int, nodo donde está el paciente
        self.hospital_destino_node_id = None  # int, elegido por el MÉDICO

        # Ruta activa elegida por el conductor
        # Es la ruta COMPLETA desde origen a destino, fija durante todo el trayecto
        self.ruta_activa_nodes = []        # List[int] — todos los nodos de la ruta
        self.ruta_activa_edges = []        # List[Edge] — todas las aristas de la ruta
        self.ruta_idx = 0                  # índice del próximo nodo a alcanzar

        # Las 3 rutas calculadas (1 por algoritmo), fijas desde el cálculo inicial
        # dict: {'Dijkstra': ScoredRoute, 'A*': ScoredRoute, 'CH': ScoredRoute}
        self.rutas_disponibles = {}
        self.ruta_activa_label = ""  # nombre del algoritmo elegido por el conductor

        # Modo ejecución
        self.modo_automatico = False
        self.tick_interval_ms = 400

        self.model = None
        self._listeners = []

    def registrar_listener(self, fn):
        self._listeners.append(fn)

    def notificar(self):
        for fn in self._listeners:
            try:
                fn()
            except Exception:
                pass

    def cambiar_fase(self, nueva_fase):
        self.fase = nueva_fase
        self.notificar()
