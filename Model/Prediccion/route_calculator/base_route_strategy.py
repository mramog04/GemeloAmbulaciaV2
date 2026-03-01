from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from Model.Prediccion.analisis_layer import ScoredRoute
    from Model.Map.RoadNetwork import RoadNetwork


class BaseRouteStrategy(ABC):
    """
    Interfaz abstracta que define el contrato para todas las estrategias
    de cálculo de rutas. Permite intercambiar algoritmos (Dijkstra, IA, etc.)
    sin modificar el resto del código (patrón Strategy).
    """

    @abstractmethod
    def calculate(self, road: 'RoadNetwork', origin_id: int, dest_id: int) -> List['ScoredRoute']:
        """
        Calcula y puntúa rutas entre dos nodos.

        Args:
            road: Instancia de RoadNetwork con los datos del grafo.
            origin_id: ID del nodo origen.
            dest_id: ID del nodo destino.

        Returns:
            Lista de ScoredRoute ordenada por score descendente (mayor score = mejor ruta).
        """
        ...
