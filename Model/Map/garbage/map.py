import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import pickle
from pathlib import Path

print("="*80)
print("🗺️  VISUALIZACIÓN DEL GRAFO PROCESADO DE LEÓN")
print("="*80)

# ================================================================================
# CARGAR DATOS
# ================================================================================

print("\n📂 Cargando archivos...")

nodes = pd.read_csv('leon_graph/nodes.csv')
edges = pd.read_csv('leon_graph/edges.csv')

# Cargar grafo NetworkX
with open('leon_graph/graph.gpickle', 'rb') as f:
    G = pickle.load(f)

print(f"   ✅ Nodos: {len(nodes)}")
print(f"   ✅ Aristas: {len(edges)}")
print(f"   ✅ Grafo NetworkX cargado")

# Hospitales - FILTRAR CORRECTAMENTE
hospitals = nodes[
    (nodes['hospital_name'].notna()) & 
    (nodes['hospital_name'] != "") & 
    (nodes['hospital_name'] != "nan")
].copy()

print(f"   ✅ Hospitales: {len(hospitals)}")

# Verificar que tenemos hospitales
if len(hospitals) == 0:
    print("\n⚠️  WARNING: No se encontraron hospitales en el grafo!")
    print("Mostrando primeras filas de nodes para debug:")
    print(nodes[['node_id', 'hospital_name', 'hospital_capacity']].head(10))

# ================================================================================
# FUNCIÓN AUXILIAR PARA OBTENER NOMBRE CORTO
# ================================================================================

def get_short_hospital_name(name):
    """Extrae un nombre corto del hospital para mostrar en el mapa"""
    if pd.isna(name) or name == "" or name == "nan":
        return "Hospital"
    
    name_str = str(name)
    
    # Si tiene guión, tomar la primera parte
    if '-' in name_str:
        return name_str.split('-')[0].strip()
    
    # Si tiene "Centro de Salud", abreviar
    if 'Centro de Salud' in name_str:
        return name_str.replace('Centro de Salud', 'CS').strip()
    
    # Si es muy largo, tomar primeras 3 palabras
    words = name_str.split()
    if len(words) > 3:
        return ' '.join(words[:3])
    
    return name_str

# ================================================================================
# VISUALIZACIÓN 1: MAPA COMPLETO SIMPLE
# ================================================================================

print("\n📊 Generando visualización 1/5: Mapa completo...")

fig, ax = plt.subplots(figsize=(12, 10))

# Dibujar todas las aristas
for _, edge in edges.iterrows():
    ax.plot(
        [edge['origin_lon'], edge['destination_lon']],
        [edge['origin_lat'], edge['destination_lat']],
        'gray', linewidth=0.5, alpha=0.6, zorder=1
    )

# Dibujar nodos
ax.scatter(nodes['lon'], nodes['lat'], c='lightblue', s=5, alpha=0.5, zorder=2)

# Dibujar hospitales
if len(hospitals) > 0:
    for _, h in hospitals.iterrows():
        ax.scatter(h['lon'], h['lat'], c='red', s=200, marker='*', 
                   edgecolors='black', linewidths=2, zorder=5)
        
        # Añadir etiqueta con nombre corto
        short_name = get_short_hospital_name(h['hospital_name'])
        ax.text(h['lon'], h['lat']+0.002, short_name, 
                fontsize=8, ha='center', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.8))

ax.set_xlabel('Longitud', fontsize=12)
ax.set_ylabel('Latitud', fontsize=12)
ax.set_title('Mapa Completo de León - Red de Calles', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('leon_map_complete.png', dpi=150, bbox_inches='tight')
print("   ✅ Guardado: leon_map_complete.png")
plt.close()

# ================================================================================
# VISUALIZACIÓN 2: MAPA COLOREADO POR TIPO DE VÍA
# ================================================================================

print("📊 Generando visualización 2/5: Mapa por tipo de vía...")

fig, ax = plt.subplots(figsize=(12, 10))

# Colorear según tipo de vía
color_map = {
    'motorway': 'red',
    'motorway_link': 'darkred',
    'trunk': 'orange',
    'trunk_link': 'darkorange',
    'primary': 'yellow',
    'primary_link': 'gold',
    'secondary': 'lightgreen',
    'secondary_link': 'green',
    'tertiary': 'lightblue',
    'residential': 'lightgray',
    'default': 'gray'
}

# Dibujar por tipo
drawn_types = set()
for _, edge in edges.iterrows():
    highway_type = edge['highway_type']
    color = color_map.get(highway_type, color_map['default'])
    
    label = highway_type if highway_type not in drawn_types else None
    if label:
        drawn_types.add(highway_type)
    
    ax.plot(
        [edge['origin_lon'], edge['destination_lon']],
        [edge['origin_lat'], edge['destination_lat']],
        color=color, linewidth=1, alpha=0.7, zorder=1, label=label
    )

# Hospitales
if len(hospitals) > 0:
    for _, h in hospitals.iterrows():
        ax.scatter(h['lon'], h['lat'], c='red', s=200, marker='*', 
                   edgecolors='black', linewidths=2, zorder=5)
        
        short_name = get_short_hospital_name(h['hospital_name'])
        ax.text(h['lon'], h['lat']+0.002, short_name, 
                fontsize=7, ha='center', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

ax.set_xlabel('Longitud', fontsize=12)
ax.set_ylabel('Latitud', fontsize=12)
ax.set_title('Mapa de León - Coloreado por Tipo de Vía', fontsize=14, fontweight='bold')
ax.legend(loc='upper right', fontsize=7, ncol=2)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('leon_map_highway_types.png', dpi=150, bbox_inches='tight')
print("   ✅ Guardado: leon_map_highway_types.png")
plt.close()

# ================================================================================
# VISUALIZACIÓN 3: MAPA DE VELOCIDADES
# ================================================================================

print("📊 Generando visualización 3/5: Mapa de velocidades...")

fig, ax = plt.subplots(figsize=(12, 10))

from matplotlib import cm
import numpy as np

speeds = edges['maxspeed_kmh'].values
norm = plt.Normalize(vmin=speeds.min(), vmax=speeds.max())
cmap = cm.get_cmap('RdYlGn_r')

for _, edge in edges.iterrows():
    color = cmap(norm(edge['maxspeed_kmh']))
    ax.plot(
        [edge['origin_lon'], edge['destination_lon']],
        [edge['origin_lat'], edge['destination_lat']],
        color=color, linewidth=1.5, alpha=0.7, zorder=1
    )

# Hospitales
if len(hospitals) > 0:
    for _, h in hospitals.iterrows():
        ax.scatter(h['lon'], h['lat'], c='blue', s=200, marker='*', 
                   edgecolors='white', linewidths=2, zorder=5)

sm = cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, fraction=0.046, pad=0.04)
cbar.set_label('Velocidad Máxima (km/h)', fontsize=11)

ax.set_xlabel('Longitud', fontsize=12)
ax.set_ylabel('Latitud', fontsize=12)
ax.set_title('Mapa de León - Velocidades Máximas', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('leon_map_speeds.png', dpi=150, bbox_inches='tight')
print("   ✅ Guardado: leon_map_speeds.png")
plt.close()

# ================================================================================
# VISUALIZACIÓN 4: MAPA DE RIESGO
# ================================================================================

print("📊 Generando visualización 4/5: Mapa de riesgo...")

fig, ax = plt.subplots(figsize=(12, 10))

risks = edges['base_risk'].values
norm_risk = plt.Normalize(vmin=0, vmax=1)
cmap_risk = cm.get_cmap('RdYlGn')

for _, edge in edges.iterrows():
    color = cmap_risk(norm_risk(edge['base_risk']))
    ax.plot(
        [edge['origin_lon'], edge['destination_lon']],
        [edge['origin_lat'], edge['destination_lat']],
        color=color, linewidth=1.5, alpha=0.7, zorder=1
    )

# Hospitales
if len(hospitals) > 0:
    for _, h in hospitals.iterrows():
        ax.scatter(h['lon'], h['lat'], c='purple', s=200, marker='*', 
                   edgecolors='white', linewidths=2, zorder=5)

sm_risk = cm.ScalarMappable(cmap=cmap_risk, norm=norm_risk)
sm_risk.set_array([])
cbar = plt.colorbar(sm_risk, ax=ax, fraction=0.046, pad=0.04)
cbar.set_label('Nivel de Riesgo (0=seguro, 1=peligroso)', fontsize=11)

ax.set_xlabel('Longitud', fontsize=12)
ax.set_ylabel('Latitud', fontsize=12)
ax.set_title('Mapa de León - Nivel de Riesgo de las Vías', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('leon_map_risk.png', dpi=150, bbox_inches='tight')
print("   ✅ Guardado: leon_map_risk.png")
plt.close()

# ================================================================================
# VISUALIZACIÓN 5: DASHBOARD COMPLETO
# ================================================================================

print("📊 Generando visualización 5/5: Dashboard completo...")

fig = plt.figure(figsize=(16, 10))
gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)

# 1. Mapa principal
ax1 = fig.add_subplot(gs[:, 0:2])
for _, edge in edges.iterrows():
    ax1.plot(
        [edge['origin_lon'], edge['destination_lon']],
        [edge['origin_lat'], edge['destination_lat']],
        'gray', linewidth=0.5, alpha=0.6
    )

if len(hospitals) > 0:
    for _, h in hospitals.iterrows():
        ax1.scatter(h['lon'], h['lat'], c='red', s=300, marker='*', 
                   edgecolors='black', linewidths=2, zorder=5)
        
        short_name = get_short_hospital_name(h['hospital_name'])
        ax1.text(h['lon'], h['lat']+0.003, short_name, 
                fontsize=9, ha='center', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.8))

ax1.set_title('Red de Calles de León', fontsize=13, fontweight='bold')
ax1.set_xlabel('Longitud', fontsize=10)
ax1.set_ylabel('Latitud', fontsize=10)
ax1.grid(True, alpha=0.3)

# 2. Distribución de tipos de vía
ax2 = fig.add_subplot(gs[0, 2])
highway_counts = edges['highway_type'].value_counts().head(8)
ax2.barh(range(len(highway_counts)), highway_counts.values, color='steelblue')
ax2.set_yticks(range(len(highway_counts)))
ax2.set_yticklabels(highway_counts.index, fontsize=8)
ax2.set_xlabel('Cantidad', fontsize=9)
ax2.set_title('Tipos de Vía', fontsize=11, fontweight='bold')
ax2.grid(True, alpha=0.3, axis='x')

# 3. Distribución de velocidades
ax3 = fig.add_subplot(gs[1, 2])
ax3.hist(edges['maxspeed_kmh'], bins=20, color='orange', edgecolor='black', alpha=0.7)
ax3.set_xlabel('Velocidad (km/h)', fontsize=9)
ax3.set_ylabel('Cantidad', fontsize=9)
ax3.set_title('Distribución de Velocidades', fontsize=11, fontweight='bold')
ax3.axvline(edges['maxspeed_kmh'].mean(), color='red', linestyle='--', linewidth=2, 
           label=f'Media: {edges["maxspeed_kmh"].mean():.1f} km/h')
ax3.legend(fontsize=8)
ax3.grid(True, alpha=0.3)

plt.suptitle('Dashboard - Grafo Procesado de León', fontsize=16, fontweight='bold', y=0.98)

plt.savefig('leon_dashboard.png', dpi=150, bbox_inches='tight')
print("   ✅ Guardado: leon_dashboard.png")
plt.close()

# ================================================================================
# ESTADÍSTICAS
# ================================================================================

print("\n" + "="*80)
print("📊 ESTADÍSTICAS DEL GRAFO")
print("="*80)

print(f"\n🗺️  General:")
print(f"   - Total de nodos: {len(nodes):,}")
print(f"   - Total de aristas: {len(edges):,}")
print(f"   - Total de hospitales: {len(hospitals)}")

print(f"\n🛣️  Tipos de vía (top 5):")
for highway, count in edges['highway_type'].value_counts().head(5).items():
    percentage = (count / len(edges)) * 100
    print(f"   - {highway:20s}: {count:4,} ({percentage:5.1f}%)")

print(f"\n⚡ Velocidades:")
print(f"   - Mínima: {edges['maxspeed_kmh'].min()} km/h")
print(f"   - Máxima: {edges['maxspeed_kmh'].max()} km/h")
print(f"   - Media: {edges['maxspeed_kmh'].mean():.1f} km/h")

print(f"\n📏 Distancias:")
print(f"   - Longitud total: {edges['length_m'].sum()/1000:.1f} km")
print(f"   - Longitud media por arista: {edges['length_m'].mean():.1f} m")

if len(hospitals) > 0:
    print(f"\n🏥 Hospitales:")
    for _, h in hospitals.iterrows():
        print(f"   - {h['hospital_name']}")
        print(f"     Nodo: {h['node_id']}")
        print(f"     Capacidad: {h['hospital_capacity']} pacientes")

print("\n" + "="*80)
print("✅ VISUALIZACIONES COMPLETADAS")
print("="*80)
print("\nArchivos generados:")
print("   📄 leon_map_complete.png")
print("   📄 leon_map_highway_types.png")
print("   📄 leon_map_speeds.png")
print("   📄 leon_map_risk.png")
print("   📄 leon_dashboard.png")

print("\n✅ ¡Listo!")