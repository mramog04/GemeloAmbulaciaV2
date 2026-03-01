import osmnx as ox
import matplotlib.pyplot as plt

# Configuración
ox.config(use_cache=True, log_console=True)

print("🗺️  Descargando datos detallados de León...")

# Descargar León
place_name = "León, Castilla y León, Spain"
G = ox.graph_from_place(place_name, network_type='drive')

print(f"✅ Descarga completa: {len(G.nodes)} nodos, {len(G.edges)} aristas\n")

# Crear figura con múltiples visualizaciones
fig, axes = plt.subplots(2, 2, figsize=(16, 16))

# 1. Vista completa básica
print("📊 Generando vista 1/4: Red completa...")
ox.plot_graph(
    G,
    ax=axes[0, 0],
    node_size=5,
    node_color='blue',
    edge_color='gray',
    edge_linewidth=0.3,
    bgcolor='white',
    show=False,
    close=False
)
axes[0, 0].set_title('1. Red Completa de León', fontsize=12, fontweight='bold')

# 2. Por tipo de vía (coloreado)
print("📊 Generando vista 2/4: Tipos de vía...")
edge_colors = []
for u, v, data in G.edges(data=True):
    if 'highway' in data:
        highway_type = data['highway']
        if isinstance(highway_type, list):
            highway_type = highway_type[0]
        
        # Colorear según tipo
        if highway_type in ['motorway', 'motorway_link']:
            edge_colors.append('red')  # Autopistas
        elif highway_type in ['trunk', 'trunk_link', 'primary', 'primary_link']:
            edge_colors.append('orange')  # Vías principales
        elif highway_type in ['secondary', 'secondary_link']:
            edge_colors.append('yellow')  # Vías secundarias
        else:
            edge_colors.append('lightgray')  # Resto
    else:
        edge_colors.append('lightgray')

ox.plot_graph(
    G,
    ax=axes[0, 1],
    node_size=0,
    edge_color=edge_colors,
    edge_linewidth=1,
    bgcolor='white',
    show=False,
    close=False
)
axes[0, 1].set_title('2. Código de Colores por Tipo de Vía\nRojo: Autopistas | Naranja: Principales | Amarillo: Secundarias', 
                     fontsize=11, fontweight='bold')

# 3. Solo vías principales (simplificado)
print("📊 Generando vista 3/4: Vías principales...")
G_simplified = G.copy()
edges_to_remove = []
for u, v, key, data in G_simplified.edges(keys=True, data=True):
    if 'highway' in data:
        highway_type = data['highway']
        if isinstance(highway_type, list):
            highway_type = highway_type[0]
        # Mantener solo autopistas y vías principales
        if highway_type not in ['motorway', 'motorway_link', 'trunk', 'trunk_link', 
                                'primary', 'primary_link', 'secondary', 'secondary_link']:
            edges_to_remove.append((u, v, key))

for edge in edges_to_remove:
    G_simplified.remove_edge(*edge)

# Remover nodos aislados
# G_simplified.remove_nodes_from(list(nx.isolates(G_simplified)))

# print(f"   Grafo simplificado: {len(G_simplified.nodes)} nodos, {len(G_simplified.edges)} aristas")

ox.plot_graph(
    G_simplified,
    ax=axes[1, 0],
    node_size=15,
    node_color='red',
    edge_color='blue',
    edge_linewidth=1.5,
    bgcolor='white',
    show=False,
    close=False
)
axes[1, 0].set_title(f'3. Solo Vías Principales\n({len(G_simplified.nodes)} nodos, {len(G_simplified.edges)} aristas)', 
                     fontsize=12, fontweight='bold')

# 4. Con puntos de interés (hospitales)
print("📊 Generando vista 4/4: Puntos de interés...")

# Buscar hospitales
try:
    hospitals = ox.geometries_from_place(place_name, tags={'amenity': 'hospital'})
    print(f"   Hospitales encontrados: {len(hospitals)}")
except:
    hospitals = None
    print("   No se pudieron cargar hospitales")

ox.plot_graph(
    G,
    ax=axes[1, 1],
    node_size=3,
    node_color='lightblue',
    edge_color='gray',
    edge_linewidth=0.3,
    bgcolor='white',
    show=False,
    close=False
)

# Marcar hospitales si se encontraron
if hospitals is not None and len(hospitals) > 0:
    for idx, row in hospitals.iterrows():
        if row.geometry.geom_type == 'Point':
            axes[1, 1].plot(row.geometry.x, row.geometry.y, 
                          'r*', markersize=20, markeredgecolor='black', markeredgewidth=1)
        elif row.geometry.geom_type == 'Polygon':
            centroid = row.geometry.centroid
            axes[1, 1].plot(centroid.x, centroid.y, 
                          'r*', markersize=20, markeredgecolor='black', markeredgewidth=1)

axes[1, 1].set_title(f'4. Red con Hospitales Marcados (★)\n{len(hospitals) if hospitals is not None else 0} hospitales encontrados', 
                     fontsize=12, fontweight='bold')

plt.tight_layout()

# Guardar
output_file = 'leon_map_detailed.png'
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"\n✅ Visualización detallada guardada en: {output_file}")

plt.show()

# Imprimir información de los hospitales
if hospitals is not None and len(hospitals) > 0:
    print("\n🏥 Hospitales encontrados en León:")
    for idx, row in hospitals.iterrows():
        name = row.get('name', 'Sin nombre')
        print(f"   - {name}")