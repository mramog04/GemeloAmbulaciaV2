import random
from Model.model_ambulance import model_ambulance
from Model.fisical_ambulance import fisical_ambulance
from Model.Map.RoadNetwork import RoadNetwork
from Model.datosGPS.gps_simulation import gps_simulation
from Model.datosMotor.engine_simulation import Engine
from Model.datosPaciente.paciente import PacienteSimulado
from Model.Prediccion.analisis_layer import AnalisisLayer
from Model.Persistencia.persistencia_layer import PersistenciaLayer

CAULE_NODE_ID = 11112307117  # Hospital de León - CAULE

class Model:
    """
    Modelo base MVC: conecta ambulancia (info+fisica), motor de red vial y simulación.
    """
    def __init__(self, 
                 roadnetwork_dir='Map/leon_graph',
                 engine_data_path='datosMotor/datasetMotor/engine_failure_dataset.csv'):
        # Carga el grafo de León
        self.road = RoadNetwork(roadnetwork_dir)
        
        # Nodo inicial SIEMPRE el del Hospital de León - CAULE
        node_ini = CAULE_NODE_ID
        pos_ini = self.road.get_node(node_ini)
        if pos_ini is None:
            raise ValueError(f"El nodo del hospital base CAULE (node_id={CAULE_NODE_ID}) no existe en la red.")

        # Datos de info estática
        self.ambulancia_info = model_ambulance(
            id_unico="AMBULANCIA-001",
            matricula="1234-ABC",
            marca="Mercedes",
            modelo="Sprinter",
            año=2022,
            tipo="UVI móvil",
            hospital_base="Hospital de León - CAULE",
            numero_bastidor="WDB1234567890X",
            equipamiento=["Desfibrilador", "Monitor multiparamétrico"],
            metadata_extra={"ultima_revision": "2026-02-01"}
        )

        # Instancias de motor, paciente, posicionamiento
        self.engine = Engine(engine_data_path)
        self.engine.start()  # Arrancamos el motor por defecto

        self.paciente = PacienteSimulado()
        self.posicion = gps_simulation(self.road, nodo_actual=node_ini)
        
        # Capa de Predicción y Análisis
        self.analisis = AnalisisLayer(self.road)
        
        # Montamos la ambulancia "física"
        self.ambulancia_fisica = fisical_ambulance(
            engine=self.engine,
            posicionamiento=self.posicion,
            paciente=self.paciente
        )

        # Capa de Persistencia
        self.persistencia = PersistenciaLayer(ruta_csv='datos_persistencia/snapshots.csv')
        self.ambulancia_info.capa_persistencia = self.persistencia

    def tick(self):
        """Simula avance de ciclo: motor, paciente, etc. Guarda snapshot en CSV."""
        self.ambulancia_fisica.tick()
        snapshot_fisico = self.ambulancia_fisica.snapshot()
        self.persistencia.guardar_snapshot(snapshot_fisico)

    def get_ruta_persistencia(self) -> str:
        """Devuelve la ruta del CSV de persistencia."""
        return self.persistencia.get_ruta_csv()

    def calcular_rutas(self, origin_id: int, dest_id: int):
        """Delega el cálculo de rutas puntuadas a la capa de análisis."""
        return self.analisis.calcular_rutas(origin_id, dest_id)

    def recomendar_hospital(self):
        """Recomienda hospitales desde la posición actual usando la capa de análisis."""
        return self.analisis.recomendar_hospital(self.posicion.nodo_actual)

    def mover_ambulancia_a(self, nuevo_node_id):
        """Actualiza el nodo/posición de la ambulancia (según la ruta)"""
        self.ambulancia_fisica.set_posicion(nuevo_node_id)

    def snapshot(self) -> dict:
        """Devuelve el estado completo actual del modelo"""
        return {
            "ambulancia_info": self.ambulancia_info.to_detailed_string(),
            "ambulancia_fisica": self.ambulancia_fisica.snapshot()
        }

    def __repr__(self):
        return f"<Model | Nodo actual: {self.posicion.nodo_actual}>"