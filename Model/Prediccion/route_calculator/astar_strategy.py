import math
from typing import List, Optional, TYPE_CHECKING
import networkx as nx

from Model.Prediccion.route_calculator.base_route_strategy import BaseRouteStrategy
from Model.Map.RoadNetwork import Route

if TYPE_CHECKING:
    from Model.Prediccion.analisis_layer import ScoredRoute
    from Model.Map.RoadNetwork import RoadNetwork


class AStarRouteStrategy(BaseRouteStrategy):
    """
    Implementación concreta de la estrategia de cálculo de rutas usando
    el algoritmo A* a través de NetworkX.

    La heurística es la distancia haversine entre el nodo actual y el
    destino, convertida a minutos asumiendo 50 km/h de velocidad media.

    Calcula tres rutas candidatas (más rápida, más corta y más segura) y
    asigna a cada una un score global ponderado entre 0.0 y 1.0.
    """

    # Pesos para el cálculo del score global
    _PESO_TIEMPO = 0.5
    _PESO_RIESGO = 0.3
    _PESO_TRAFICO = 0.2

    # ------------------------------------------------------------------ #
    # Métodos internos de construcción del grafo                           #
    # ------------------------------------------------------------------ #

    def _build_nx_graph(self, road: 'RoadNetwork', weight: str = 'current_time_min') -> nx.MultiDiGraph:
        """
        Construye un grafo NetworkX a partir de los nodos y aristas de la red.

        Args:
            road: Instancia de RoadNetwork.
            weight: Atributo a usar como peso ('current_time_min', 'length_m', 'base_risk').

        Returns:
            Grafo NetworkX MultiDiGraph listo para calcular rutas.
        """
        G = nx.MultiDiGraph()

        for node_id, node in road.nodes.items():
            G.add_node(node_id,
                       lat=node.lat,
                       lon=node.lon,
                       is_hospital=node.is_hospital())

        for edge in road.all_edges:
            if weight == 'current_time_min':
                edge_weight = edge.current_time_min
            elif weight == 'length_m':
                edge_weight = edge.length_m
            elif weight == 'base_risk':
                edge_weight = edge.get_risk_score()
            else:
                edge_weight = edge.current_time_min

            if edge.is_blocked:
                edge_weight = float('inf')

            G.add_edge(
                edge.origin.node_id,
                edge.destination.node_id,
                key=edge.edge_id,
                weight=edge_weight,
                length_m=edge.length_m,
                current_time_min=edge.current_time_min,
                base_risk=edge.base_risk,
                traffic_factor=edge.traffic_factor,
                edge_object=edge
            )

        return G

    def _heuristic(self, u, v, G, dest_id):
        """Estima minutos restantes desde u hasta dest_id usando haversine."""
        lat1, lon1 = G.nodes[u]['lat'], G.nodes[u]['lon']
        lat2, lon2 = G.nodes[dest_id]['lat'], G.nodes[dest_id]['lon']
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        dist_km = R * 2 * math.asin(math.sqrt(a))
        return (dist_km / 50.0) * 60.0  # minutos a 50 km/h

    def _calculate_route(self,
                         road: 'RoadNetwork',
                         origin_id: int,
                         dest_id: int,
                         weight: str = 'current_time_min') -> Optional[Route]:
        """
        Calcula la ruta óptima entre dos nodos para un criterio de peso dado
        usando el algoritmo A*.

        Args:
            road: Instancia de RoadNetwork.
            origin_id: ID del nodo origen.
            dest_id: ID del nodo destino.
            weight: Criterio de optimización.

        Returns:
            Objeto Route o None si no existe camino.
        """
        if origin_id not in road.nodes or dest_id not in road.nodes:
            print(f"❌ Error: Nodo origen o destino no existe")
            return None

        G = self._build_nx_graph(road, weight=weight)

        try:
            node_path = nx.astar_path(
                G, origin_id, dest_id,
                heuristic=lambda u, v: self._heuristic(u, v, G, dest_id),
                weight='weight'
            )

            edges = []
            total_distance = 0.0
            total_time = 0.0
            total_risk = 0.0
            total_traffic = 0.0

            for i in range(len(node_path) - 1):
                u = node_path[i]
                v = node_path[i + 1]
                edge = road.get_edge(u, v)
                if edge:
                    edges.append(edge)
                    total_distance += edge.length_m
                    total_time += edge.current_time_min
                    total_risk += edge.get_risk_score()
                    total_traffic += edge.traffic_factor

            num_edges = len(edges)
            avg_traffic = total_traffic / num_edges if num_edges > 0 else 1.0

            return Route(
                nodes=node_path,
                edges=edges,
                total_distance_m=total_distance,
                total_time_min=total_time,
                total_risk=total_risk / num_edges if num_edges > 0 else 0.0,
                avg_traffic_factor=avg_traffic
            )

        except nx.NetworkXNoPath:
            print(f"❌ No hay camino entre {origin_id} y {dest_id}")
            return None
        except Exception as e:
            print(f"❌ Error calculando ruta (A*): {e}")
            return None

    # ------------------------------------------------------------------ #
    # Implementación del contrato                                          #
    # ------------------------------------------------------------------ #

    def calculate(self, road: 'RoadNetwork', origin_id: int, dest_id: int) -> List['ScoredRoute']:
        """
        Calcula tres rutas candidatas (tiempo, distancia, seguridad) usando A*
        y las puntúa con un score global ponderado.

        Args:
            road: Instancia de RoadNetwork con los datos del grafo.
            origin_id: ID del nodo origen.
            dest_id: ID del nodo destino.

        Returns:
            Lista de ScoredRoute ordenada por score descendente.
        """
        from Model.Prediccion.analisis_layer import ScoredRoute

        candidatos = []

        route_tiempo = self._calculate_route(road, origin_id, dest_id, weight='current_time_min')
        if route_tiempo:
            candidatos.append((route_tiempo, "Más rápida (A*)"))

        route_dist = self._calculate_route(road, origin_id, dest_id, weight='length_m')
        if route_dist and (not candidatos or route_dist.nodes != candidatos[0][0].nodes):
            candidatos.append((route_dist, "Más corta (A*)"))

        route_segura = self._calculate_route(road, origin_id, dest_id, weight='base_risk')
        if route_segura and route_segura.nodes not in [c[0].nodes for c in candidatos]:
            candidatos.append((route_segura, "Más segura (A*)"))

        if not candidatos:
            return []

        # Normalizar métricas para calcular scores
        tiempos = [r.total_time_min for r, _ in candidatos]
        riesgos = [r.total_risk for r, _ in candidatos]
        traficos = [r.avg_traffic_factor for r, _ in candidatos]

        max_tiempo = max(tiempos) if max(tiempos) > 0 else 1.0
        max_riesgo = max(riesgos) if max(riesgos) > 0 else 1.0
        max_trafico = max(traficos) if max(traficos) > 0 else 1.0

        # Calcular penalización ponderada para cada candidato
        penalizaciones = []
        for ruta, _ in candidatos:
            norm_tiempo = ruta.total_time_min / max_tiempo
            norm_riesgo = ruta.total_risk / max_riesgo
            norm_trafico = ruta.avg_traffic_factor / max_trafico
            penalizacion = (
                self._PESO_TIEMPO * norm_tiempo
                + self._PESO_RIESGO * norm_riesgo
                + self._PESO_TRAFICO * norm_trafico
            )
            penalizaciones.append(penalizacion)

        min_p = min(penalizaciones)
        max_p = max(penalizaciones)
        rango = max_p - min_p if max_p > min_p else 1.0

        scored = []
        for (ruta, label), penalizacion in zip(candidatos, penalizaciones):
            score = round(1.0 - (penalizacion - min_p) / rango, 4)

            scored.append(ScoredRoute(
                route=ruta,
                score=score,
                label=label,
                breakdown={
                    'tiempo': round(ruta.total_time_min, 3),
                    'riesgo': round(ruta.total_risk, 3),
                    'trafico': round(ruta.avg_traffic_factor, 3)
                }
            ))

        scored.sort(key=lambda s: s.score, reverse=True)
        return scored
