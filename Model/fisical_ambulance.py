from typing import Optional
from Model.datosMotor.engine_simulation import Engine
from Model.datosPaciente.paciente import PacienteSimulado
from Model.datosGPS.gps_simulation import gps_simulation

class fisical_ambulance:
    """
    Capa Física del Gemelo Digital para la ambulancia.
    Orquesta el motor, el paciente y el posicionamiento (basado en el grafo de ciudad/red vial).
    Provee métodos de snapshot y actualización conjunta.
    """
    def __init__(self,
                 engine: Engine,
                 posicionamiento: gps_simulation,
                 paciente: Optional[PacienteSimulado] = None):
        """
        Inicializa la ambulancia física.

        Args:
            engine: Simulador Engine (motor).
            posicionamiento: PosicionamientoSimulado acoplado a RoadNetwork.
            paciente: PacienteSimulado (si no, se crea automáticamente).
        """
        self.engine = engine
        self.posicionamiento = posicionamiento
        self.paciente = paciente if paciente is not None else PacienteSimulado()

    def tick(self, avanzar_nodo_id: Optional[int] = None):
        """
        Ciclo principal de simulación.
        - Actualiza el motor (tick)
        - Opcionalmente mueve la ambulancia a otro nodo (si se pasa el id)
        - Actualiza el estado del paciente

        Args:
            avanzar_nodo_id: node_id al que avanzar la ambulancia en esta iteración (opcional)
        """
        self.engine.tick()
        if avanzar_nodo_id is not None:
            self.set_posicion(avanzar_nodo_id)
        self.paciente.actualizar_estado()

    def set_posicion(self, id_nodo: int):
        """
        Actualiza la posición de la ambulancia a un nuevo nodo.
        """
        self.posicionamiento.avanzar_a_nodo(id_nodo)

    def get_current_node(self) -> int:
        """
        Devuelve el node_id actual de la ambulancia.
        """
        return self.posicionamiento.nodo_actual

    def snapshot(self) -> dict:
        """
        Devuelve el estado físico de la ambulancia para logging o vistas.
        """
        return {
            "engine": self.engine.get_telemetry(),
            "paciente": self.paciente.get_telemetria(),
            "posicion": self.posicionamiento.get_posicion()
        }

    def __repr__(self):
        node_info = self.posicionamiento.get_posicion()
        return (
            f"[FISICAL AMBULANCE] nodo={node_info['node_id'] if node_info else 'N/A'} | "
            f"coordenadas={node_info['coordenadas'] if node_info else 'N/A'} | "
            f"Paciente: {self.paciente} | Engine: {self.engine}"
        )