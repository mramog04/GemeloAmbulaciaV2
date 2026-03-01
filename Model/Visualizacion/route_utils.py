from Model.Prediccion.route_calculator.dijkstra_strategy import DijkstraRouteStrategy

try:
    from Model.Prediccion.route_calculator.astar_strategy import AStarRouteStrategy
    _ASTAR_AVAILABLE = True
except ImportError:
    _ASTAR_AVAILABLE = False

try:
    from Model.Prediccion.route_calculator.ch_strategy import CHRouteStrategy
    _CH_AVAILABLE = True
except ImportError:
    _CH_AVAILABLE = False


def _construir_ruta_custom(road, origin_id, dest_id, edge_weight_fn, label, score=0.5):
    """Helper: construye una ScoredRoute usando pesos personalizados via networkx."""
    from Model.Prediccion.analisis_layer import ScoredRoute
    from Model.Map.RoadNetwork import Route
    import networkx as nx

    G = nx.MultiDiGraph()
    for node_id, node in road.nodes.items():
        G.add_node(node_id, lat=node.lat, lon=node.lon)
    for edge in road.all_edges:
        w = edge_weight_fn(edge)
        if edge.is_blocked:
            w = float('inf')
        G.add_edge(edge.origin.node_id, edge.destination.node_id,
                   key=edge.edge_id, weight=w)
    try:
        node_path = nx.shortest_path(G, origin_id, dest_id, weight='weight')
        dist = tiempo = risk = traffic = 0.0
        edges = []
        for i in range(len(node_path) - 1):
            e = road.get_edge(node_path[i], node_path[i + 1])
            if e:
                edges.append(e)
                dist += e.length_m
                tiempo += e.current_time_min
                risk += e.get_risk_score()
                traffic += e.traffic_factor
        n = len(edges) or 1
        ruta = Route(
            nodes=node_path, edges=edges,
            total_distance_m=dist, total_time_min=tiempo,
            total_risk=risk / n, avg_traffic_factor=traffic / n
        )
        return ScoredRoute(
            route=ruta, score=score, label=label,
            breakdown={
                'tiempo': round(tiempo, 3),
                'riesgo': round(risk / n, 3),
                'trafico': round(traffic / n, 3),
            }
        )
    except Exception:
        return None


def calcular_5_rutas(analisis_layer, origin_id, dest_id):
    """
    Genera hasta 5 ScoredRoute con diferentes criterios usando DijkstraRouteStrategy
    (y A*/CH si están disponibles).

    Estrategia:
    - Ruta 1: Dijkstra optimizando tiempo              → label "Más rápida"
    - Ruta 2: Dijkstra optimizando distancia           → label "Más corta"
    - Ruta 3: Dijkstra optimizando seguridad           → label "Más segura"
    - Ruta 4: A* si disponible, si no Dijkstra mixto   → label "A* óptima" / "Equilibrada"
    - Ruta 5: CH si disponible, si no Dijkstra tráfico → label "CH óptima" / "Bajo tráfico"

    Devuelve lista de ScoredRoute (máx 5, deduplicando rutas idénticas por nodos).
    """
    road = analisis_layer.road
    dijkstra = DijkstraRouteStrategy()
    resultados = []
    nodos_vistos = []

    def _agregar(scored_route):
        if scored_route and scored_route.route:
            nodes = scored_route.route.nodes
            if nodes not in nodos_vistos:
                nodos_vistos.append(nodes)
                resultados.append(scored_route)

    # Rutas 1-3: Dijkstra con distintos criterios
    base_rutas = dijkstra.calculate(road, origin_id, dest_id)
    for sr in base_rutas:
        _agregar(sr)

    # Ruta 4: A* o Dijkstra equilibrado
    if _ASTAR_AVAILABLE:
        try:
            astar = AStarRouteStrategy()
            rutas_astar = astar.calculate(road, origin_id, dest_id)
            if rutas_astar:
                sr = rutas_astar[0]
                sr_new = ScoredRoute(
                    route=sr.route,
                    score=sr.score,
                    label="A* óptima",
                    breakdown=sr.breakdown
                )
                _agregar(sr_new)
        except Exception:
            pass
    else:
        # Dijkstra con peso combinado: 0.7*tiempo + 0.3*riesgo
        sr = _construir_ruta_custom(
            road, origin_id, dest_id,
            edge_weight_fn=lambda e: 0.7 * e.current_time_min + 0.3 * e.get_risk_score(),
            label="Equilibrada"
        )
        _agregar(sr)

    # Ruta 5: CH o Dijkstra bajo tráfico
    if _CH_AVAILABLE:
        try:
            ch = CHRouteStrategy()
            rutas_ch = ch.calculate(road, origin_id, dest_id)
            if rutas_ch:
                sr = rutas_ch[0]
                sr_new = ScoredRoute(
                    route=sr.route,
                    score=sr.score,
                    label="CH óptima",
                    breakdown=sr.breakdown
                )
                _agregar(sr_new)
        except Exception:
            pass
    else:
        # Dijkstra penalizando tráfico
        sr = _construir_ruta_custom(
            road, origin_id, dest_id,
            edge_weight_fn=lambda e: e.current_time_min * e.traffic_factor,
            label="Bajo tráfico"
        )
        _agregar(sr)

    return resultados[:5]
