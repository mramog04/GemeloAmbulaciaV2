import osmnx as ox
import matplotlib.pyplot as plt

# Configuración de osmnx
ox.config(use_cache=True, log_console=True)

print("🗺️  Descargando datos de León, España desde OpenStreetMap...")

# Descargar el grafo de calles de León
try:
    # Opción 1: Por nombre de ciudad
    place_name = "León, Castilla y León, Spain"
    G = ox.graph_from_place(place_name, network_type='drive')
    
    print(f"✅ Grafo descargado exitosamente")
    print(f"   - Nodos (intersecciones): {len(G.nodes)}")
    print(f"   - Aristas (calles): {len(G.edges)}")
    
    # Visualizar el grafo completo
    print("\n📊 Generando visualización...")
    
    fig, ax = plt.subplots(figsize=(12, 12))
    ox.plot_graph(
        G, 
        ax=ax,
        node_size=10,
        node_color='red',
        edge_color='gray',
        edge_linewidth=0.5,
        bgcolor='white',
        show=False,
        close=False
    )
    
    ax.set_title('Red de Calles de León (OpenStreetMap)', fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    # Guardar imagen
    output_file = 'leon_map.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Mapa guardado en: {output_file}")
    
    # Mostrar
    plt.show()
    
    # Información adicional
    print("\n📋 Información del grafo:")
    print(f"   - Tipo de grafo: {type(G)}")
    print(f"   - Es dirigido: {G.is_directed()}")
    print(f"   - Es multigrafo: {G.is_multigraph()}")
    
    # Obtener estadísticas básicas
    stats = ox.basic_stats(G)
    print(f"\n📊 Estadísticas básicas:")
    print(f"   - Número de nodos: {stats['n']}")
    print(f"   - Número de aristas: {stats['m']}")
    print(f"   - Longitud total de calles: {stats['street_length_total']/1000:.2f} km")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nIntentando con método alternativo...")
    
    # Opción 2: Por coordenadas (centro de León)
    try:
        # Coordenadas del centro de León (Plaza Mayor)
        center_point = (42.5987, -5.5671)
        G = ox.graph_from_point(center_point, dist=5000, network_type='drive')
        
        print(f"✅ Grafo descargado (radio 5km desde centro)")
        print(f"   - Nodos: {len(G.nodes)}")
        print(f"   - Aristas: {len(G.edges)}")
        
        fig, ax = plt.subplots(figsize=(12, 12))
        ox.plot_graph(
            G,
            ax=ax,
            node_size=10,
            node_color='red',
            edge_color='gray',
            edge_linewidth=0.5,
            bgcolor='white',
            show=False,
            close=False
        )
        
        ax.set_title('Red de Calles de León - Radio 5km desde centro', fontsize=16)
        plt.tight_layout()
        
        output_file = 'leon_map_center.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Mapa guardado en: {output_file}")
        
        plt.show()
        
    except Exception as e2:
        print(f"❌ Error en método alternativo: {e2}")