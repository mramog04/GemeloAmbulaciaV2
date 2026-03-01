import osmnx as ox
import pandas as pd
import networkx as nx
import json
import re
from datetime import datetime
from pathlib import Path
import pickle
# Configuración
ox.config(use_cache=True, log_console=True)

# ================================================================================
# CONFIGURACIÓN DE VALORES POR DEFECTO
# ================================================================================

SPEED_DEFAULTS = {
    'motorway': 120,
    'motorway_link': 80,
    'trunk': 100,
    'trunk_link': 70,
    'primary': 50,
    'primary_link': 40,
    'secondary': 50,
    'secondary_link': 40,
    'tertiary': 40,
    'tertiary_link': 30,
    'residential': 30,
    'living_street': 20,
    'service': 20,
    'unclassified': 40,
    'road': 30,
    'default': 30
}

LANES_DEFAULTS = {
    'motorway': 3,
    'motorway_link': 1,
    'trunk': 2,
    'trunk_link': 1,
    'primary': 2,
    'primary_link': 1,
    'secondary': 1,
    'secondary_link': 1,
    'tertiary': 1,
    'tertiary_link': 1,
    'residential': 1,
    'living_street': 1,
    'service': 1,
    'unclassified': 1,
    'road': 1,
    'default': 1
}

RISK_DEFAULTS = {
    'motorway': 0.1,
    'motorway_link': 0.2,
    'trunk': 0.15,
    'trunk_link': 0.25,
    'primary': 0.3,
    'primary_link': 0.3,
    'secondary': 0.4,
    'secondary_link': 0.4,
    'tertiary': 0.5,
    'tertiary_link': 0.5,
    'residential': 0.6,
    'living_street': 0.7,
    'service': 0.5,
    'unclassified': 0.5,
    'road': 0.6,
    'default': 0.5
}

SURFACE_DEFAULTS = {
    'asphalt': 1.0,
    'paved': 0.9,
    'concrete': 0.95,
    'cobblestone': 0.6,
    'unpaved': 0.4,
    'gravel': 0.3,
    'dirt': 0.2,
    'default': 0.85
}

# ================================================================================
# HOSPITALES DE LEÓN
# ================================================================================

HOSPITALS = [
    {
        "name": "Hospital de León - CAULE",
        "lat": 42.6134,
        "lon": -5.5701,
        "capacity": 100,
        "specialties": "general;trauma;cardio;neuro;pediatria",
        "emergency": True
    },
    {
        "name": "Hospital San Juan de Dios",
        "lat": 42.5987,
        "lon": -5.5671,
        "capacity": 50,
        "specialties": "general;geriatria;rehabilitacion",
        "emergency": True
    },
    {
        "name": "Centro de Salud Armunia",
        "lat": 42.5812,
        "lon": -5.5623,
        "capacity": 20,
        "specialties": "general;pediatria",
        "emergency": False
    },
    {
        "name": "Centro de Salud La Condesa",
        "lat": 42.6045,
        "lon": -5.5834,
        "capacity": 20,
        "specialties": "general",
        "emergency": False
    }
]

# ================================================================================
# FUNCIONES AUXILIARES
# ================================================================================

def extract_number(value):
    """Extrae un número de un string"""
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        match = re.search(r'\d+', value)
        if match:
            return int(match.group())
    return None

def clean_maxspeed(maxspeed_value, highway_type):
    """Limpia y normaliza el valor de maxspeed"""
    if maxspeed_value is None:
        return SPEED_DEFAULTS.get(highway_type, SPEED_DEFAULTS['default'])
    
    if isinstance(maxspeed_value, list):
        maxspeed_value = maxspeed_value[0]
    
    if isinstance(maxspeed_value, (int, float)):
        return int(maxspeed_value)
    
    maxspeed_str = str(maxspeed_value).lower()
    
    # Casos especiales
    if 'none' in maxspeed_str or 'signals' in maxspeed_str:
        return SPEED_DEFAULTS.get(highway_type, SPEED_DEFAULTS['default'])
    elif 'es:urban' in maxspeed_str or 'urban' in maxspeed_str:
        return 50
    elif 'es:rural' in maxspeed_str or 'rural' in maxspeed_str:
        return 90
    elif 'walk' in maxspeed_str:
        return 10
    
    # Extraer número
    number = extract_number(maxspeed_str)
    if number:
        # Si es mph, convertir a km/h
        if 'mph' in maxspeed_str:
            return int(number * 1.60934)
        return number
    
    return SPEED_DEFAULTS.get(highway_type, SPEED_DEFAULTS['default'])

def clean_lanes(lanes_value, highway_type):
    """Limpia y normaliza el valor de lanes"""
    if lanes_value is None:
        return LANES_DEFAULTS.get(highway_type, LANES_DEFAULTS['default'])
    
    if isinstance(lanes_value, list):
        lanes_value = lanes_value[0]
    
    try:
        return int(lanes_value)
    except:
        return LANES_DEFAULTS.get(highway_type, LANES_DEFAULTS['default'])

def get_highway_type(highway_value):
    """Extrae el tipo de highway"""
    if isinstance(highway_value, list):
        return highway_value[0]
    return highway_value

def get_surface_quality(surface_value):
    """Calcula la calidad de la superficie"""
    if surface_value is None:
        return SURFACE_DEFAULTS['default']
    
    if isinstance(surface_value, list):
        surface_value = surface_value[0]
    
    surface_str = str(surface_value).lower()
    return SURFACE_DEFAULTS.get(surface_str, SURFACE_DEFAULTS['default'])

def get_street_name(name_value):
    """Limpia el nombre de la calle"""
    if name_value is None:
        return ""
    
    if isinstance(name_value, list):
        return " | ".join(str(n) for n in name_value)
    
    return str(name_value)

# ================================================================================
# PROCESAMIENTO PRINCIPAL
# ================================================================================

def analyze_completeness(G):
    """Analiza la completitud de los datos"""
    print("\n" + "="*80)
    print("🔍 ANÁLISIS DE COMPLETITUD")
    print("="*80)
    
    total_edges = len(G.edges)
    
    fields = ['length', 'highway', 'maxspeed', 'lanes', 'oneway', 'name', 'surface']
    completeness = {}
    
    for field in fields:
        count = sum(1 for u, v, k, data in G.edges(data=True, keys=True) if field in data and data[field] is not None)
        percentage = (count / total_edges) * 100
        completeness[field] = count
        
        icon = "✅" if percentage > 90 else "⚠️" if percentage > 50 else "❌"
        print(f"   {field:15s} : {count:6d} / {total_edges:6d} ({percentage:5.1f}%) {icon}")
    
    return completeness

def process_edges(G):
    """Procesa todas las aristas del grafo"""
    print("\n" + "="*80)
    print("🛠️  PROCESANDO ARISTAS")
    print("="*80)
    
    stats = {
        'removed': 0,
        'maxspeed_filled': 0,
        'lanes_filled': 0,
        'surface_calculated': 0,
        'base_time_calculated': 0,
        'base_risk_assigned': 0
    }
    
    edges_to_remove = []
    
    for u, v, key, data in G.edges(data=True, keys=True):
        # 1. Verificar length (obligatorio)
        if 'length' not in data or data['length'] <= 0:
            edges_to_remove.append((u, v, key))
            stats['removed'] += 1
            continue
        
        # 2. Verificar highway (obligatorio)
        if 'highway' not in data:
            edges_to_remove.append((u, v, key))
            stats['removed'] += 1
            continue
        
        highway_type = get_highway_type(data['highway'])
        
        # 3. Procesar maxspeed
        original_maxspeed = data.get('maxspeed')
        data['maxspeed_kmh'] = clean_maxspeed(original_maxspeed, highway_type)
        if original_maxspeed is None:
            stats['maxspeed_filled'] += 1
        
        # 4. Procesar lanes
        original_lanes = data.get('lanes')
        data['lanes'] = clean_lanes(original_lanes, highway_type)
        if original_lanes is None:
            stats['lanes_filled'] += 1
        
        # 5. Procesar oneway
        if 'oneway' not in data:
            data['oneway'] = False
        
        # 6. Procesar surface_quality
        data['surface_quality'] = get_surface_quality(data.get('surface'))
        stats['surface_calculated'] += 1
        
        # 7. Calcular base_time_min
        length_km = data['length'] / 1000
        speed_kmh = data['maxspeed_kmh']
        data['base_time_min'] = (length_km / speed_kmh) * 60
        stats['base_time_calculated'] += 1
        
        # 8. Asignar base_risk
        data['base_risk'] = RISK_DEFAULTS.get(highway_type, RISK_DEFAULTS['default'])
        stats['base_risk_assigned'] += 1
        
        # 9. Has coverage (True por defecto en León)
        data['has_coverage'] = True
        
        # 10. Limpiar street_name
        data['street_name'] = get_street_name(data.get('name'))
        
        # 11. Guardar highway_type limpio
        data['highway_type'] = highway_type
    
    # Eliminar aristas inválidas
    for edge in edges_to_remove:
        G.remove_edge(*edge)
    
    print(f"   - Aristas eliminadas (sin length/highway): {stats['removed']}")
    print(f"   - maxspeed rellenados: {stats['maxspeed_filled']}")
    print(f"   - lanes rellenados: {stats['lanes_filled']}")
    print(f"   - surface_quality calculados: {stats['surface_calculated']}")
    print(f"   - base_time calculados: {stats['base_time_calculated']}")
    print(f"   - base_risk asignados: {stats['base_risk_assigned']}")
    
    return stats

def process_nodes(G):
    """Procesa todos los nodos del grafo"""
    print("\n" + "="*80)
    print("🏥 PROCESANDO NODOS Y HOSPITALES")
    print("="*80)
    
    # Inicializar todos los nodos sin hospital
    for node in G.nodes:
        G.nodes[node]['hospital_name'] = ""
        G.nodes[node]['hospital_capacity'] = 0
        G.nodes[node]['hospital_specialties'] = ""
        G.nodes[node]['hospital_emergency'] = False
    
    # Asignar hospitales
    hospital_nodes = []
    for hospital in HOSPITALS:
        # Encontrar nodo más cercano
        nearest_node = ox.distance.nearest_nodes(G, hospital['lon'], hospital['lat'])
        
        # Asignar atributos del hospital al nodo
        G.nodes[nearest_node]['hospital_name'] = hospital['name']
        G.nodes[nearest_node]['hospital_capacity'] = hospital['capacity']
        G.nodes[nearest_node]['hospital_specialties'] = hospital['specialties']
        G.nodes[nearest_node]['hospital_emergency'] = hospital['emergency']
        
        hospital_nodes.append({
            'name': hospital['name'],
            'node_id': nearest_node,
            'lat': G.nodes[nearest_node]['y'],
            'lon': G.nodes[nearest_node]['x'],
            'original_lat': hospital['lat'],
            'original_lon': hospital['lon']
        })
        
        print(f"   ✅ {hospital['name']}")
        print(f"      → nodo {nearest_node} ({G.nodes[nearest_node]['y']:.6f}, {G.nodes[nearest_node]['x']:.6f})")
    
    return hospital_nodes

def validate_graph(G):
    """Valida que el grafo procesado sea correcto"""
    print("\n" + "="*80)
    print("✔️  VALIDANDO DATOS")
    print("="*80)
    
    errors = []
    warnings = []
    
    for u, v, key, data in G.edges(data=True, keys=True):
        # Validar campos obligatorios
        if data.get('length', 0) <= 0:
            errors.append(f"Arista {u}-{v}: length inválido")
        
        if data.get('maxspeed_kmh', 0) <= 0 or data.get('maxspeed_kmh', 0) > 150:
            warnings.append(f"Arista {u}-{v}: maxspeed sospechoso ({data.get('maxspeed_kmh')})")
        
        if data.get('lanes', 0) < 1 or data.get('lanes', 0) > 6:
            warnings.append(f"Arista {u}-{v}: lanes sospechoso ({data.get('lanes')})")
        
        if not (0 <= data.get('base_risk', -1) <= 1):
            errors.append(f"Arista {u}-{v}: base_risk fuera de rango")
        
        if not (0 <= data.get('surface_quality', -1) <= 1):
            errors.append(f"Arista {u}-{v}: surface_quality fuera de rango")
        
        if data.get('base_time_min', 0) <= 0:
            errors.append(f"Arista {u}-{v}: base_time_min inválido")
    
    if errors:
        print(f"   ❌ ERRORES encontrados: {len(errors)}")
        for error in errors[:10]:  # Mostrar solo los primeros 10
            print(f"      - {error}")
    else:
        print(f"   ✅ No se encontraron errores")
    
    if warnings:
        print(f"   ⚠️  ADVERTENCIAS: {len(warnings)}")
        for warning in warnings[:5]:  # Mostrar solo las primeras 5
            print(f"      - {warning}")
    else:
        print(f"   ✅ No se encontraron advertencias")
    
    return len(errors) == 0

# Reemplaza la función export_to_csv completa con esta versión corregida:

def export_to_csv(G, hospital_nodes, output_dir):
    """Exporta el grafo procesado a archivos CSV"""
    print("\n" + "="*80)
    print("💾 EXPORTANDO ARCHIVOS")
    print("="*80)
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # 1. NODES.CSV
    nodes_data = []
    for node, data in G.nodes(data=True):
        nodes_data.append({
            'node_id': node,
            'lat': data['y'],
            'lon': data['x'],
            'hospital_name': data.get('hospital_name', ""),
            'hospital_capacity': data.get('hospital_capacity', 0),
            'hospital_specialties': data.get('hospital_specialties', ""),
            'hospital_emergency': data.get('hospital_emergency', False)
        })
    
    nodes_df = pd.DataFrame(nodes_data)
    nodes_csv = output_path / 'nodes.csv'
    nodes_df.to_csv(nodes_csv, index=False, encoding='utf-8')
    print(f"   ✅ {nodes_csv} ({len(nodes_df)} nodos)")
    
    # 2. EDGES.CSV
    edges_data = []
    edge_id = 0
    for u, v, key, data in G.edges(data=True, keys=True):
        edge_id += 1
        edges_data.append({
            'edge_id': edge_id,
            'origin_id': u,
            'destination_id': v,
            'key': key,
            'street_name': data.get('street_name', ""),
            'highway_type': data.get('highway_type', ""),
            'length_m': round(data.get('length', 0), 2),
            'lanes': data.get('lanes', 1),
            'maxspeed_kmh': data.get('maxspeed_kmh', 30),
            'oneway': data.get('oneway', False),
            'base_time_min': round(data.get('base_time_min', 0), 4),
            'base_risk': round(data.get('base_risk', 0.5), 3),
            'surface_quality': round(data.get('surface_quality', 0.85), 3),
            'has_coverage': data.get('has_coverage', True),
            'origin_lat': G.nodes[u]['y'],
            'origin_lon': G.nodes[u]['x'],
            'destination_lat': G.nodes[v]['y'],
            'destination_lon': G.nodes[v]['x']
        })
    
    edges_df = pd.DataFrame(edges_data)
    edges_csv = output_path / 'edges.csv'
    edges_df.to_csv(edges_csv, index=False, encoding='utf-8')
    print(f"   ✅ {edges_csv} ({len(edges_df)} aristas)")
    
    # 3. METADATA.JSON - Calcular bbox manualmente
    all_lats = [data['y'] for node, data in G.nodes(data=True)]
    all_lons = [data['x'] for node, data in G.nodes(data=True)]
    
    bbox = {
        'north': max(all_lats),
        'south': min(all_lats),
        'east': max(all_lons),
        'west': min(all_lons)
    }
    
    metadata = {
        'city': 'León',
        'region': 'Castilla y León',
        'country': 'Spain',
        'processed_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_nodes': len(G.nodes),
        'total_edges': len(G.edges),
        'total_hospitals': len(hospital_nodes),
        'hospitals': hospital_nodes,
        'bbox': bbox,
        'default_speeds': SPEED_DEFAULTS,
        'risk_levels': RISK_DEFAULTS
    }
    
    metadata_json = output_path / 'metadata.json'
    with open(metadata_json, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"   ✅ {metadata_json}")
    
    # 4. GRAPH.GPICKLE
    graph_pickle = output_path / 'graph.gpickle'
    with open(graph_pickle, 'wb') as f:
        pickle.dump(G, f, pickle.HIGHEST_PROTOCOL)
    print(f"   ✅ {graph_pickle}")
    
    return nodes_df, edges_df, metadata

def generate_report(G, completeness_before, processing_stats, hospital_nodes, output_dir):
    """Genera reporte de procesamiento"""
    report_lines = []
    
    report_lines.append("="*80)
    report_lines.append("REPORTE DE PROCESAMIENTO DEL GRAFO DE LEÓN")
    report_lines.append("="*80)
    report_lines.append(f"\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    report_lines.append("\n" + "="*80)
    report_lines.append("📊 ESTADÍSTICAS INICIALES")
    report_lines.append("="*80)
    report_lines.append(f"   - Nodos totales: {len(G.nodes):,}")
    report_lines.append(f"   - Aristas totales: {len(G.edges):,}")
    
    report_lines.append("\n" + "="*80)
    report_lines.append("🔍 COMPLETITUD ANTES DEL PROCESAMIENTO")
    report_lines.append("="*80)
    total_edges = len(G.edges)
    for field, count in completeness_before.items():
        percentage = (count / total_edges) * 100
        report_lines.append(f"   - {field:15s} : {count:6,} / {total_edges:6,} ({percentage:5.1f}%)")
    
    report_lines.append("\n" + "="*80)
    report_lines.append("🛠️  PROCESAMIENTO REALIZADO")
    report_lines.append("="*80)
    report_lines.append(f"   - Aristas eliminadas: {processing_stats['removed']}")
    report_lines.append(f"   - maxspeed rellenados: {processing_stats['maxspeed_filled']:,}")
    report_lines.append(f"   - lanes rellenados: {processing_stats['lanes_filled']:,}")
    report_lines.append(f"   - surface_quality calculados: {processing_stats['surface_calculated']:,}")
    report_lines.append(f"   - base_time calculados: {processing_stats['base_time_calculated']:,}")
    report_lines.append(f"   - base_risk asignados: {processing_stats['base_risk_assigned']:,}")
    
    report_lines.append("\n" + "="*80)
    report_lines.append("🏥 HOSPITALES ASIGNADOS")
    report_lines.append("="*80)
    for h in hospital_nodes:
        report_lines.append(f"   - {h['name']}")
        report_lines.append(f"     → Nodo: {h['node_id']}")
        report_lines.append(f"     → Coordenadas: ({h['lat']:.6f}, {h['lon']:.6f})")
    
    report_lines.append("\n" + "="*80)
    report_lines.append("📊 ESTADÍSTICAS FINALES")
    report_lines.append("="*80)
    report_lines.append(f"   - Nodos procesados: {len(G.nodes):,}")
    report_lines.append(f"   - Aristas procesadas: {len(G.edges):,}")
    report_lines.append(f"   - Completitud: 100% ✅")
    
    report_lines.append("\n" + "="*80)
    report_lines.append("✅ PROCESAMIENTO COMPLETADO EXITOSAMENTE")
    report_lines.append("="*80)
    
    report_text = "\n".join(report_lines)
    
    # Guardar reporte
    report_file = Path(output_dir) / 'processing_report.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    print(report_text)
    print(f"\n   ✅ Reporte guardado en: {report_file}")

# ================================================================================
# MAIN
# ================================================================================

def main():
    print("\n" + "="*80)
    print("🗺️  PROCESADOR DE GRAFO DE LEÓN")
    print("="*80)
    
    # 1. Descargar grafo
    print("\n📥 Descargando grafo de León desde OpenStreetMap...")
    place_name = "León, Castilla y León, Spain"
    G = ox.graph_from_place(place_name, network_type='drive')
    print(f"   ✅ Descargado: {len(G.nodes):,} nodos, {len(G.edges):,} aristas")
    
    # 2. Analizar completitud inicial
    completeness_before = analyze_completeness(G)
    
    # 3. Procesar aristas
    processing_stats = process_edges(G)
    
    # 4. Procesar nodos y hospitales
    hospital_nodes = process_nodes(G)
    
    # 5. Validar
    if not validate_graph(G):
        print("\n❌ El grafo tiene errores. Revisa los mensajes anteriores.")
        return
    
    # 6. Exportar
    output_dir = 'leon_graph'
    nodes_df, edges_df, metadata = export_to_csv(G, hospital_nodes, output_dir)
    
    # 7. Generar reporte
    generate_report(G, completeness_before, processing_stats, hospital_nodes, output_dir)
    
    print("\n" + "="*80)
    print("🎉 ¡PROCESAMIENTO COMPLETADO!")
    print("="*80)
    print(f"\n📁 Archivos generados en: {output_dir}/")
    print("   - nodes.csv")
    print("   - edges.csv")
    print("   - metadata.json")
    print("   - graph.gpickle")
    print("   - processing_report.txt")
    print("\n🚀 ¡Listo para usar en el gemelo digital!")

if __name__ == "__main__":
    main()