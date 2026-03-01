import time
from Model.MainModel import Model
from Model.Prediccion.route_calculator.astar_strategy import AStarRouteStrategy
from Model.Prediccion.route_calculator.ch_strategy import CHRouteStrategy

def main():
    print("="*60)
    print("🚑 GEMELO DIGITAL POC: TEST DE MÓDULO MODELO")
    print("="*60)

    # Inicializa el modelo
    model = Model(roadnetwork_dir='Model/Map/leon_graph', engine_data_path='Model/datosMotor/datasetMotor/engine_failure_dataset.csv')
    print("\n📍 Nodo inicial:", model.posicion.nodo_actual)
    print("Coordenadas:", model.posicion.get_posicion()["coordenadas"])

    # Selecciona hospital destino (el más cercano distinto al inicial)
    all_hospitals = [n for n in model.road.get_hospitals()]
    destino = None
    for h in all_hospitals:
        if h.node_id != model.posicion.nodo_actual:
            destino = h
            break
    if not destino:
        print("No hay hospital alternativo. Salida de test.")
        return

    print(f"\n🏥 Nodo destino: {destino.hospital.name} ({destino.node_id})")
    print("Coordenadas destino:", (destino.lat, destino.lon))

    # Calcula la ruta
    print("\n🔍 Calculando ruta...")
    scored_routes = model.analisis.calcular_rutas(model.posicion.nodo_actual, destino.node_id)
    if not scored_routes:
        print("No se pudo calcular ruta.")
        return

    mejor = scored_routes[0]
    print(f"   → Ruta seleccionada: {mejor.label} (score={mejor.score:.4f})")
    route = mejor.route
    model.road.print_route_details(route)

    print("\n🟢 Iniciando trayecto SIMULADO nodo a nodo...\n")
    for idx, node_id in enumerate(route.nodes[1:], 1):
        # Mueve la ambulancia
        model.mover_ambulancia_a(node_id)
        model.tick()

        estado = model.snapshot()
        nodeinfo = model.road.get_node(node_id)
        coords = (nodeinfo.lat, nodeinfo.lon)
        print(f"🟡 [{idx}/{len(route.nodes)-1}] Nodo actual: {node_id} - Coordenadas: {coords}")
        print(f"   → FC paciente: {estado['ambulancia_fisica']['paciente']['fc']}  -   Temp motor: {estado['ambulancia_fisica']['engine']['temperature']}")
        time.sleep(0.1)  # Simular tiempo real (puedes quitarlo o ajustarlo)

    print("\n✅ Ruta completada. Nodo final:", model.posicion.nodo_actual)
    print("Snapshot final:", model.snapshot())

    # === COMPARATIVA DE ESTRATEGIAS DE RUTA ===
    print("\n" + "="*50)
    print("=== COMPARATIVA DE ESTRATEGIAS DE RUTA ===")
    print("="*50)

    origin = model.posicion.nodo_actual

    from Model.Prediccion.route_calculator.dijkstra_strategy import DijkstraRouteStrategy

    configs = [
        ("Dijkstra", DijkstraRouteStrategy()),
        ("A*",       AStarRouteStrategy()),
        ("CH",       CHRouteStrategy()),
    ]

    for nombre, estrategia in configs:
        rutas = estrategia.calculate(model.road, origin, destino.node_id)
        if rutas:
            mejor_r = rutas[0]
            print(f"{nombre:<10}: {len(rutas)} rutas → mejor: \"{mejor_r.label}\" "
                  f"(score={mejor_r.score:.4f}, tiempo={mejor_r.breakdown['tiempo']:.1f}min)")
        else:
            print(f"{nombre:<10}: sin rutas calculadas")

    print(f"\n💾 Snapshots guardados: {model.persistencia.get_total_ticks()} → {model.get_ruta_persistencia()}")

if __name__ == "__main__":
    main()