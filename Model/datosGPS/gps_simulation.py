class gps_simulation:
    """
    Gestiona el posicionamiento de la ambulancia a partir de node_id
    y expone la posición consultando a RoadNetwork.
    """
    def __init__(self, road_network, nodo_actual: int):
        """
        Args:
            road_network: instancia de RoadNetwork ya cargada.
            nodo_actual: node_id inicial de la ambulancia.
        """
        self.road_network = road_network
        self.nodo_actual = nodo_actual

    def avanzar_a_nodo(self, nuevo_nodo_id: int):
        """Actualiza la posición"""
        if self.road_network.get_node(nuevo_nodo_id):
            self.nodo_actual = nuevo_nodo_id
        else:
            raise ValueError(f"El nodo {nuevo_nodo_id} no existe en la red.")

    def get_posicion(self):
        """Devuelve información útil: node_id y coordenadas."""
        nodo = self.road_network.get_node(self.nodo_actual)
        if nodo is None:
            return None
        return {
            "node_id": nodo.node_id,
            "coordenadas": (nodo.lat, nodo.lon)
        }

    def __repr__(self):
        data = self.get_posicion()
        if data is not None:
            return f"(Nodo: {data['node_id']}, Coordenadas: {data['coordenadas']})"
        return "(Posición desconocida)"