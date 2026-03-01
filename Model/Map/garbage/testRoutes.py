from RoadNetwork import RoadNetwork
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import cm
import numpy as np

print("="*80)
print("🗺️  TEST DE RUTAS CON VISUALIZACIÓN")
print("="*80)

# ============================================================================
# CARGAR RED Y DATOS
# ============================================================================

network = RoadNetwork('leon_graph')
nodes_df = pd.read_csv('leon_graph/nodes.csv')
edges_df = pd.read_csv('leon_graph/edges.csv')

# Obtener hospitales
hospitals = network.get_hospitals()
print(f"\n🏥 Hospitales disponibles: {len(hospitals)}")
for h in hospitals:
    print(f"   - {h.hospital.name} (nodo {h.node_id})")

# ============================================================================
# SELECCIONAR PUNTOS DE ORIGEN Y DESTINO
# ============================================================================

# Origen: Un nodo aleatorio del centro de León
origin_node_id = 593264750  # Puedes cambiar esto

# Destino: Hospital CAULE
hospital_caule = None
for h in hospitals:
    if "CAULE" in h.hospital.name:
        hospital_caule = h
        break

if not hospital_caule:
    hospital_caule = hospitals[0]  # Tomar el primero si no encuentra CAULE

destination_node_id = hospital_caule.node_id

print(f"\n📍 Origen: Nodo {origin_node_id}")
print(f"📍 Destino: {hospital_caule.hospital.name} (nodo {destination_node_id})")

# ============================================================================
# CALCULAR RUTAS
# ============================================================================

print("\n🔍 Calculando rutas...")

# Calcular 3 rutas alternativas
routes = network.calculate_multiple_routes(origin_node_id, destination_node_id, num_routes=3)

print(f"\n✅ Se calcularon {len(routes)} rutas:")
for i, route in enumerate(routes, 1):
    print(f"   Ruta {i}: {route.get_total_distance_km():.2f} km, "
          f"{route.total_time_min:.1f} min, "
          f"riesgo={route.total_risk:.2f}")

# ============================================================================
# VISUALIZACIÓN 1: RUTA PRINCIPAL
# ============================================================================

print("\n📊 Generando visualización 1/4: Ruta principal...")

fig, ax = plt.subplots(figsize=(14, 12))

# Dibujar todas las calles en gris claro
for _, edge in edges_df.iterrows():
    ax.plot(
        [edge['origin_lon'], edge['destination_lon']],
        [edge['origin_lat'], edge['destination_lat']],
        'lightgray', linewidth=0.3, alpha=0.5, zorder=1
    )

# Dibujar la ruta principal
if routes:
    route = routes[0]
    route_coords = []
    
    for node_id in route.nodes:
        node = network.get_node(node_id)
        route_coords.append((node.lon, node.lat))
    
    route_x = [c[0] for c in route_coords]
    route_y = [c[1] for c in route_coords]
    
    # Dibujar la ruta con línea gruesa azul
    ax.plot(route_x, route_y, 'b-', linewidth=4, alpha=0.8, zorder=3, label='Ruta calculada')
    
    # Marcar nodos de la ruta
    ax.scatter(route_x, route_y, c='blue', s=30, alpha=0.6, zorder=4)
    
    # Marcar origen y destino
    origin_node = network.get_node(origin_node_id)
    dest_node = network.get_node(destination_node_id)
    
    ax.scatter(origin_node.lon, origin_node.lat, 
              c='green', s=500, marker='o', edgecolors='black', linewidths=3, 
              zorder=5, label='Origen')
    
    ax.scatter(dest_node.lon, dest_node.lat, 
              c='red', s=500, marker='*', edgecolors='black', linewidths=3, 
              zorder=5, label='Destino (Hospital)')
    
    # Etiquetas
    ax.text(origin_node.lon, origin_node.lat + 0.003, 'ORIGEN', 
            fontsize=10, ha='center', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgreen', alpha=0.9))
    
    ax.text(dest_node.lon, dest_node.lat + 0.003, dest_node.hospital.name.split('-')[0].strip(), 
            fontsize=10, ha='center', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='lightcoral', alpha=0.9))
    
    # Información de la ruta
    info_text = f"Distancia: {route.get_total_distance_km():.2f} km\n"
    info_text += f"Tiempo: {route.total_time_min:.1f} min\n"
    info_text += f"Nodos: {len(route.nodes)}"
    
    ax.text(0.02, 0.98, info_text, transform=ax.transAxes,
            fontsize=11, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9))

# Marcar otros hospitales
for h in hospitals:
    if h.node_id != destination_node_id:
        ax.scatter(h.lon, h.lat, c='orange', s=200, marker='*', 
                  edgecolors='black', linewidths=2, zorder=5, alpha=0.5)

ax.set_xlabel('Longitud', fontsize=12)
ax.set_ylabel('Latitud', fontsize=12)
ax.set_title('Ruta Calculada - León', fontsize=14, fontweight='bold')
ax.legend(loc='upper right', fontsize=10)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('route_main.png', dpi=150, bbox_inches='tight')
print("   ✅ Guardado: route_main.png")
plt.close()

# ============================================================================
# VISUALIZACIÓN 2: MÚLTIPLES RUTAS ALTERNATIVAS
# ============================================================================

print("📊 Generando visualización 2/4: Rutas alternativas...")

fig, ax = plt.subplots(figsize=(14, 12))

# Dibujar todas las calles
for _, edge in edges_df.iterrows():
    ax.plot(
        [edge['origin_lon'], edge['destination_lon']],
        [edge['origin_lat'], edge['destination_lat']],
        'lightgray', linewidth=0.3, alpha=0.5, zorder=1
    )

# Colores para las rutas
route_colors = ['blue', 'green', 'purple']
route_labels = ['Ruta 1 (Más rápida)', 'Ruta 2 (Alternativa)', 'Ruta 3 (Alternativa)']

# Dibujar todas las rutas
for idx, route in enumerate(routes):
    route_coords = []
    
    for node_id in route.nodes:
        node = network.get_node(node_id)
        route_coords.append((node.lon, node.lat))
    
    route_x = [c[0] for c in route_coords]
    route_y = [c[1] for c in route_coords]
    
    color = route_colors[idx % len(route_colors)]
    label = route_labels[idx % len(route_labels)]
    
    ax.plot(route_x, route_y, color=color, linewidth=3, alpha=0.6, 
            zorder=3+idx, label=label)

# Marcar origen y destino
origin_node = network.get_node(origin_node_id)
dest_node = network.get_node(destination_node_id)

ax.scatter(origin_node.lon, origin_node.lat, 
          c='green', s=500, marker='o', edgecolors='black', linewidths=3, 
          zorder=10, label='Origen')

ax.scatter(dest_node.lon, dest_node.lat, 
          c='red', s=500, marker='*', edgecolors='black', linewidths=3, 
          zorder=10, label='Hospital')

# Crear leyenda con información de rutas
legend_text = "Rutas calculadas:\n"
for i, route in enumerate(routes, 1):
    legend_text += f"\nRuta {i}:\n"
    legend_text += f"  {route.get_total_distance_km():.2f} km\n"
    legend_text += f"  {route.total_time_min:.1f} min\n"
    legend_text += f"  Riesgo: {route.total_risk:.2f}"

ax.text(0.02, 0.98, legend_text, transform=ax.transAxes,
        fontsize=9, verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9))

ax.set_xlabel('Longitud', fontsize=12)
ax.set_ylabel('Latitud', fontsize=12)
ax.set_title('Rutas Alternativas - León', fontsize=14, fontweight='bold')
ax.legend(loc='upper right', fontsize=9)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('route_alternatives.png', dpi=150, bbox_inches='tight')
print("   ✅ Guardado: route_alternatives.png")
plt.close()

# ============================================================================
# VISUALIZACIÓN 3: RUTA CON MAPA DE TRÁFICO
# ============================================================================

print("📊 Generando visualización 3/4: Ruta con mapa de tráfico...")

fig, ax = plt.subplots(figsize=(14, 12))

# Dibujar calles coloreadas por tráfico
for _, edge_row in edges_df.iterrows():
    # Simular factor de tráfico (puedes usar el real si actualizas el network)
    traffic_factor = 1.0  # Por ahora, tráfico normal
    
    # Color según tráfico: verde=fluido, amarillo=normal, rojo=congestionado
    if traffic_factor < 1.2:
        color = 'green'
        alpha = 0.3
    elif traffic_factor < 1.5:
        color = 'yellow'
        alpha = 0.4
    else:
        color = 'red'
        alpha = 0.5
    
    ax.plot(
        [edge_row['origin_lon'], edge_row['destination_lon']],
        [edge_row['origin_lat'], edge_row['destination_lat']],
        color=color, linewidth=0.5, alpha=alpha, zorder=1
    )

# Dibujar la ruta principal
if routes:
    route = routes[0]
    route_coords = []
    
    for node_id in route.nodes:
        node = network.get_node(node_id)
        route_coords.append((node.lon, node.lat))
    
    route_x = [c[0] for c in route_coords]
    route_y = [c[1] for c in route_coords]
    
    ax.plot(route_x, route_y, 'blue', linewidth=5, alpha=0.9, zorder=3, 
            label='Ruta calculada', linestyle='--')
    
    # Marcar cada calle de la ruta con su factor de tráfico
    for edge in route.edges:
        mid_x = (edge.origin.lon + edge.destination.lon) / 2
        mid_y = (edge.origin.lat + edge.destination.lat) / 2
        
        # Color según tráfico
        if edge.traffic_factor < 1.2:
            marker_color = 'green'
        elif edge.traffic_factor < 1.5:
            marker_color = 'orange'
        else:
            marker_color = 'red'
        
        ax.scatter(mid_x, mid_y, c=marker_color, s=50, 
                  edgecolors='black', linewidths=1, zorder=4)

# Marcar origen y destino
origin_node = network.get_node(origin_node_id)
dest_node = network.get_node(destination_node_id)

ax.scatter(origin_node.lon, origin_node.lat, 
          c='green', s=500, marker='o', edgecolors='black', linewidths=3, 
          zorder=10)

ax.scatter(dest_node.lon, dest_node.lat, 
          c='red', s=500, marker='*', edgecolors='black', linewidths=3, 
          zorder=10)

ax.set_xlabel('Longitud', fontsize=12)
ax.set_ylabel('Latitud', fontsize=12)
ax.set_title('Ruta con Estado del Tráfico', fontsize=14, fontweight='bold')

# Leyenda de colores
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor='green', alpha=0.5, label='Tráfico fluido (<1.2x)'),
    Patch(facecolor='yellow', alpha=0.5, label='Tráfico normal (1.2-1.5x)'),
    Patch(facecolor='red', alpha=0.5, label='Tráfico congestionado (>1.5x)'),
    plt.Line2D([0], [0], color='blue', linewidth=5, linestyle='--', label='Ruta calculada')
]
ax.legend(handles=legend_elements, loc='upper right', fontsize=9)

ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('route_traffic.png', dpi=150, bbox_inches='tight')
print("   ✅ Guardado: route_traffic.png")
plt.close()

# ============================================================================
# VISUALIZACIÓN 4: ZOOM EN LA RUTA
# ============================================================================

print("📊 Generando visualización 4/4: Zoom en la ruta...")

if routes:
    route = routes[0]
    
    # Calcular límites del zoom (bounding box de la ruta + margen)
    route_lats = [network.get_node(nid).lat for nid in route.nodes]
    route_lons = [network.get_node(nid).lon for nid in route.nodes]
    
    lat_min, lat_max = min(route_lats), max(route_lats)
    lon_min, lon_max = min(route_lons), max(route_lons)
    
    # Añadir margen del 10%
    lat_margin = (lat_max - lat_min) * 0.1
    lon_margin = (lon_max - lon_min) * 0.1
    
    fig, ax = plt.subplots(figsize=(14, 12))
    
    # Dibujar solo calles en el área de la ruta
    for _, edge in edges_df.iterrows():
        # Verificar si la arista está en el área
        if (lon_min - lon_margin <= edge['origin_lon'] <= lon_max + lon_margin and
            lat_min - lat_margin <= edge['origin_lat'] <= lat_max + lat_margin):
            
            ax.plot(
                [edge['origin_lon'], edge['destination_lon']],
                [edge['origin_lat'], edge['destination_lat']],
                'lightgray', linewidth=1, alpha=0.6, zorder=1
            )
    
    # Dibujar la ruta con números en cada segmento
    route_coords = []
    for node_id in route.nodes:
        node = network.get_node(node_id)
        route_coords.append((node.lon, node.lat))
    
    route_x = [c[0] for c in route_coords]
    route_y = [c[1] for c in route_coords]
    
    ax.plot(route_x, route_y, 'b-', linewidth=5, alpha=0.8, zorder=3)
    
    # Numerar cada segmento
    for i, edge in enumerate(route.edges, 1):
        mid_x = (edge.origin.lon + edge.destination.lon) / 2
        mid_y = (edge.origin.lat + edge.destination.lat) / 2
        
        ax.text(mid_x, mid_y, str(i), fontsize=8, ha='center', 
               fontweight='bold', color='white',
               bbox=dict(boxstyle='circle', facecolor='blue', alpha=0.8))
    
    # Marcar todos los nodos de la ruta
    ax.scatter(route_x, route_y, c='blue', s=80, edgecolors='white', 
              linewidths=2, zorder=4)
    
    # Marcar origen y destino
    ax.scatter(route_x[0], route_y[0], 
              c='green', s=600, marker='o', edgecolors='black', linewidths=3, 
              zorder=5)
    
    ax.scatter(route_x[-1], route_y[-1], 
              c='red', s=600, marker='*', edgecolors='black', linewidths=3, 
              zorder=5)
    
    # Información detallada de cada segmento
    info_text = "Segmentos de la ruta:\n\n"
    for i, edge in enumerate(route.edges[:5], 1):  # Mostrar primeros 5
        name = edge.street_name if edge.street_name else "Sin nombre"
        info_text += f"{i}. {name[:20]}\n"
        info_text += f"   {edge.length_m:.0f}m, {edge.current_time_min:.1f}min\n"
    
    if len(route.edges) > 5:
        info_text += f"\n... y {len(route.edges)-5} segmentos más"
    
    ax.text(0.02, 0.98, info_text, transform=ax.transAxes,
            fontsize=8, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9))
    
    # Establecer límites del zoom
    ax.set_xlim(lon_min - lon_margin, lon_max + lon_margin)
    ax.set_ylim(lat_min - lat_margin, lat_max + lat_margin)
    
    ax.set_xlabel('Longitud', fontsize=12)
    ax.set_ylabel('Latitud', fontsize=12)
    ax.set_title('Zoom en la Ruta Calculada', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('route_zoom.png', dpi=150, bbox_inches='tight')
    print("   ✅ Guardado: route_zoom.png")
    plt.close()

# ============================================================================
# RESUMEN
# ============================================================================

print("\n" + "="*80)
print("✅ VISUALIZACIONES COMPLETADAS")
print("="*80)
print("\nArchivos generados:")
print("   📄 route_main.png - Ruta principal resaltada")
print("   📄 route_alternatives.png - Múltiples rutas alternativas")
print("   📄 route_traffic.png - Ruta con mapa de tráfico")
print("   📄 route_zoom.png - Zoom detallado en la ruta")

# Imprimir detalles de la ruta principal
if routes:
    print("\n" + "="*80)
    print("📍 DETALLES DE LA RUTA PRINCIPAL")
    print("="*80)
    network.print_route_details(routes[0])

print("\n✅ ¡Test completado!")