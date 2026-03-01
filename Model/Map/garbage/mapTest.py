from RoadNetwork import RoadNetwork

print("="*80)
print("🧪 TEST: RoadNetwork con Clases Node y Edge")
print("="*80)

# 1. Cargar red
print("\n1️⃣ Cargando red...")
road = RoadNetwork('leon_graph')
print(road)

# 2. Consultar un nodo
print("\n2️⃣ Consultar nodo:")
some_node = list(road.nodes.values())[0]
print(f"   {some_node}")
print(f"   Coordenadas: {some_node.get_coordinates()}")
print(f"   Es hospital: {some_node.is_hospital()}")
print(f"   Aristas salientes: {len(some_node.outgoing_edges)}")
print(f"   Aristas entrantes: {len(some_node.incoming_edges)}")

# 3. Hospitales
print("\n3️⃣ Hospitales:")
hospitals = road.get_hospitals()
for h_node in hospitals:
    print(f"   {h_node}")
    print(f"      Hospital: {h_node.hospital}")
    print(f"      Especialidades: {', '.join(h_node.hospital.specialties)}")
    print(f"      Urgencias 24h: {h_node.hospital.has_emergency}")
    print()

# 4. Consultar arista
print("\n4️⃣ Consultar arista:")
if some_node.outgoing_edges:
    edge = some_node.outgoing_edges[0]
    print(f"   {edge}")
    print(f"   Longitud: {edge.get_length_km():.3f} km")
    print(f"   Velocidad máxima: {edge.maxspeed_kmh} km/h")
    print(f"   Carriles: {edge.lanes}")
    print(f"   Tipo: {edge.highway_type}")
    print(f"   Tiempo base: {edge.base_time_min:.2f} min")
    print(f"   Tiempo actual: {edge.get_travel_time():.2f} min")
    print(f"   Factor tráfico: {edge.traffic_factor}")
    print(f"   Riesgo: {edge.get_risk_score():.3f}")
    print(f"   Es autopista: {edge.is_highway()}")

# 5. Vecinos de un nodo
print("\n5️⃣ Vecinos de un nodo:")
neighbors = some_node.get_neighbors()
print(f"   Nodo: {some_node.node_id}")
print(f"   Vecinos: {len(neighbors)}")
for neighbor in neighbors[:5]:
    dist = some_node.distance_to(neighbor)
    print(f"      → Nodo {neighbor.node_id} (dist: {dist:.3f} km)")

# 6. Actualizar tráfico
print("\n6️⃣ Simular tráfico:")
if some_node.outgoing_edges:
    edge = some_node.outgoing_edges[0]
    print(f"   Arista: {edge.origin.node_id} → {edge.destination.node_id}")
    print(f"   Tiempo inicial: {edge.current_time_min:.2f} min")
    
    # Simular atasco
    edge.update_traffic(2.5)
    print(f"   Tiempo con atasco (factor 2.5x): {edge.current_time_min:.2f} min")
    
    # Bloquear calle
    edge.block()
    print(f"   Calle bloqueada: {edge.is_blocked}")
    print(f"   Tiempo: {edge.current_time_min}")

# 7. Distancia entre nodos
print("\n7️⃣ Distancia entre hospitales:")
if len(hospitals) >= 2:
    h1 = hospitals[0]
    h2 = hospitals[1]
    dist = h1.distance_to(h2)
    print(f"   {h1.hospital.name}")
    print(f"   ↓ {dist:.3f} km")
    print(f"   {h2.hospital.name}")

# 8. Encontrar hospital más cercano
print("\n8️⃣ Hospital más cercano:")
test_node = list(road.nodes.values())[100]
nearest_hospital = road.get_nearest_hospital(test_node)
if nearest_hospital:
    dist = test_node.distance_to(nearest_hospital)
    print(f"   Desde nodo: {test_node.node_id}")
    print(f"   Hospital más cercano: {nearest_hospital.hospital.name}")
    print(f"   Distancia: {dist:.3f} km")

# 9. Estadísticas
print("\n9️⃣ Estadísticas:")
stats = road.get_stats()
for key, value in stats.items():
    print(f"   {key}: {value}")

print("\n" + "="*80)
print("✅ TEST COMPLETADO")
print("="*80)