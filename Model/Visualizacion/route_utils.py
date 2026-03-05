from Model.Prediccion.route_calculator.dijkstra_strategy import DijkstraRouteStrategy
from Model.Prediccion.route_calculator.astar_strategy import AStarRouteStrategy
from Model.Prediccion.route_calculator.ch_strategy import CHRouteStrategy
from Model.Prediccion.analisis_layer import ScoredRoute


def calcular_rutas_por_algoritmo(road, origin_id, dest_id):
    """
    Calcula 3 rutas diferenciadas por criterio de optimización.

    Devuelve dict: {
        'Más rápida': ScoredRoute,  # optimizada por tiempo (Dijkstra)
        'Más corta':  ScoredRoute,  # optimizada por distancia (A*)
        'Más segura': ScoredRoute,  # optimizada por riesgo (CH)
    }
    Solo incluye la entrada si el algoritmo consigue calcular una ruta válida.
    """
    resultado = {}

    dijkstra = DijkstraRouteStrategy()
    astar = AStarRouteStrategy()
    ch = CHRouteStrategy()

    criterios = [
        ('Más rápida', dijkstra, 'current_time_min'),
        ('Más corta',  astar,    'length_m'),
        ('Más segura', ch,       'base_risk'),
    ]

    for label, estrategia, weight in criterios:
        try:
            ruta = estrategia._calculate_route(road, origin_id, dest_id, weight=weight)
            if ruta:
                scored = ScoredRoute(
                    route=ruta,
                    score=0.0,
                    label=label,
                    breakdown={
                        'tiempo': round(ruta.total_time_min, 3),
                        'riesgo': round(ruta.total_risk, 3),
                        'trafico': round(ruta.avg_traffic_factor, 3),
                    }
                )
                resultado[label] = scored
        except Exception as e:
            print(f"⚠️ Criterio '{label}' falló: {e}")

    return resultado
