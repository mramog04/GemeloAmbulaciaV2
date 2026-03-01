from dataclasses import dataclass
from typing import List, Optional, TYPE_CHECKING

from Model.Map.RoadNetwork import RoadNetwork, Route
from Model.Prediccion.route_calculator.base_route_strategy import BaseRouteStrategy
from Model.Prediccion.route_calculator.dijkstra_strategy import DijkstraRouteStrategy


@dataclass
class ScoredRoute:
    """
    Ruta calculada junto con su puntuación y metadatos de evaluación.

    Atributos:
        route: Objeto Route con la secuencia de nodos y aristas.
        score: Puntuación global de 0.0 (peor) a 1.0 (mejor aptitud).
        label: Etiqueta descriptiva ('Más rápida', 'Más segura', 'Más corta').
        breakdown: Desglose de métricas usadas para calcular el score.
    """
    route: Route
    score: float
    label: str
    breakdown: dict

    def __repr__(self):
        return (f"ScoredRoute(label='{self.label}', score={self.score:.4f}, "
                f"tiempo={self.breakdown.get('tiempo', 0):.1f}min)")


class AnalisisLayer:
    """
    Orquestador principal de la Capa de Predicción y Análisis.

    Consume un grafo de red vial (RoadNetwork) y una estrategia de cálculo
    de rutas inyectada (patrón Strategy) para exponer servicios de análisis
    de alto nivel.

    Atributos:
        road: Red de calles sobre la que operar.
        estrategia: Algoritmo de cálculo de rutas a usar.
    """

    def __init__(self,
                 road: RoadNetwork,
                 estrategia: Optional[BaseRouteStrategy] = None):
        """
        Inicializa la capa de análisis.

        Args:
            road: Instancia de RoadNetwork con los datos del grafo.
            estrategia: Estrategia de cálculo de rutas. Si no se indica,
                        se usa DijkstraRouteStrategy por defecto.
        """
        self.road = road
        self.estrategia: BaseRouteStrategy = estrategia or DijkstraRouteStrategy()

    def set_estrategia(self, estrategia: BaseRouteStrategy) -> None:
        """
        Permite cambiar la estrategia de rutas en tiempo de ejecución.

        Args:
            estrategia: Nueva instancia de BaseRouteStrategy a usar.
        """
        self.estrategia = estrategia

    # ------------------------------------------------------------------ #
    # Métodos públicos de análisis de rutas                                #
    # ------------------------------------------------------------------ #

    def calcular_rutas(self, origin_id: int, dest_id: int) -> List[ScoredRoute]:
        """
        Calcula y puntúa rutas entre dos nodos usando la estrategia activa.

        Args:
            origin_id: ID del nodo origen.
            dest_id: ID del nodo destino.

        Returns:
            Lista de ScoredRoute ordenada por score descendente.
        """
        return self.estrategia.calculate(self.road, origin_id, dest_id)

    def recomendar_mejor_ruta(self, origin_id: int, dest_id: int) -> Optional[ScoredRoute]:
        """
        Devuelve únicamente la ruta con mayor score entre dos nodos.

        Args:
            origin_id: ID del nodo origen.
            dest_id: ID del nodo destino.

        Returns:
            ScoredRoute con mayor score, o None si no hay ruta posible.
        """
        rutas = self.calcular_rutas(origin_id, dest_id)
        return rutas[0] if rutas else None

    def recomendar_hospital(self, origin_id: int) -> List[ScoredRoute]:
        """
        Para cada hospital de la red, calcula la mejor ruta desde el nodo
        indicado y devuelve la lista ordenada por score descendente.

        Args:
            origin_id: ID del nodo desde el que parte la ambulancia.

        Returns:
            Lista de ScoredRoute (una por hospital alcanzable) ordenada
            por score descendente.
        """
        hospitales = self.road.get_hospitals()
        resultados: List[ScoredRoute] = []

        for hospital_node in hospitales:
            if hospital_node.node_id == origin_id:
                continue
            mejor = self.recomendar_mejor_ruta(origin_id, hospital_node.node_id)
            if mejor:
                resultados.append(mejor)

        resultados.sort(key=lambda s: s.score, reverse=True)
        return resultados

    # ------------------------------------------------------------------ #
    # Huecos para futuros módulos de IA                                    #
    # ------------------------------------------------------------------ #

    # TODO: predecir_fallo_mecanico(self, telemetria: dict) -> dict:
    #   Módulo de predicción de fallos mecánicos basado en datos del motor.
    #   Recibirá la telemetría actual y devolverá probabilidad y tipo de fallo.

    # TODO: detectar_anomalia_clinica(self, signos_vitales: dict) -> dict:
    #   Módulo de detección de anomalías clínicas del paciente.
    #   Analizará FC, SpO2, temperatura, etc. y alertará sobre eventos críticos.
