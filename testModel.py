import time
from Model.MainModel import Model

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
    route = model.road.calculate_route(model.posicion.nodo_actual, destino.node_id)
    if not route:
        print("No se pudo calcular ruta.")
        return

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

if __name__ == "__main__":
    main()