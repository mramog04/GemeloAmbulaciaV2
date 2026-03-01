from Model.Prediccion.route_calculator.dijkstra_strategy import DijkstraRouteStrategy
from Model.Prediccion.route_calculator.astar_strategy import AStarRouteStrategy
from Model.Prediccion.route_calculator.ch_strategy import CHRouteStrategy


def calcular_rutas_por_algoritmo(road, origin_id, dest_id):
    """
    Calcula una ruta por cada algoritmo disponible.

    Devuelve dict: {
        'Dijkstra': ScoredRoute,
        'A*': ScoredRoute,
        'CH': ScoredRoute,
    }
    Solo incluye la entrada si el algoritmo consigue calcular una ruta válida.
    """
    resultado = {}

    estrategias = [
        ('Dijkstra', DijkstraRouteStrategy()),
        ('A*', AStarRouteStrategy()),
        ('CH', CHRouteStrategy()),
    ]

    for nombre, estrategia in estrategias:
        try:
            rutas = estrategia.calculate(road, origin_id, dest_id)
            if rutas:
                mejor = max(rutas, key=lambda r: r.score)
                mejor.label = nombre
                resultado[nombre] = mejor
        except Exception as e:
            print(f"⚠️ Algoritmo {nombre} falló: {e}")

    return resultado
