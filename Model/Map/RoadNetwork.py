import pandas as pd
import networkx as nx
import json
import pickle
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import numpy as np

# ============================================================================
# CLASE HOSPITAL
# ============================================================================

@dataclass
class Hospital:
    """Representa un hospital en un nodo"""
    name: str
    capacity: int
    specialties: List[str]
    has_emergency: bool
    current_patients: int = 0  # NUEVO: Pacientes actuales
    
    def __repr__(self):
        return f"Hospital({self.name}, {self.current_patients}/{self.capacity})"
    
    def can_handle_emergency(self) -> bool:
        """Verifica si el hospital tiene urgencias 24h"""
        return self.has_emergency
    
    def has_specialty(self, specialty: str) -> bool:
        """Verifica si el hospital tiene una especialidad"""
        return specialty in self.specialties
    
    # NUEVOS MÉTODOS
    def is_full(self) -> bool:
        """Verifica si el hospital está a capacidad máxima"""
        return self.current_patients >= self.capacity
    
    def get_available_beds(self) -> int:
        """Retorna número de camas disponibles"""
        return max(0, self.capacity - self.current_patients)
    
    def accept_patient(self) -> bool:
        """Intenta aceptar un paciente. Retorna True si hay espacio."""
        if not self.is_full():
            self.current_patients += 1
            return True
        return False
    
    def release_patient(self) -> None:
        """Libera un paciente (decrementar contador)"""
        if self.current_patients > 0:
            self.current_patients -= 1
    
    def can_treat_affliction(self, affliction: str, afflictions_db: Dict) -> bool:
        """
        Verifica si el hospital puede tratar una afección específica.
        
        Args:
            affliction: Nombre de la afección
            afflictions_db: Base de datos de afecciones
            
        Returns:
            True si el hospital tiene las especialidades necesarias
        """
        if affliction not in afflictions_db:
            return False
        
        required_specialties = afflictions_db[affliction].get('specialties_required', [])
        
        # El hospital debe tener al menos una de las especialidades requeridas
        return any(self.has_specialty(spec) for spec in required_specialties)
    
    def get_occupancy_percentage(self) -> float:
        """Retorna porcentaje de ocupación"""
        if self.capacity == 0:
            return 0.0
        return (self.current_patients / self.capacity) * 100

# ============================================================================
# CLASE ROUTE
# ============================================================================

@dataclass
class Route:
    """Representa una ruta calculada entre dos nodos"""
    nodes: List[int]  # Lista de IDs de nodos
    edges: List['Edge']  # Lista de aristas a recorrer
    total_distance_m: float
    total_time_min: float
    total_risk: float
    avg_traffic_factor: float
    
    def get_total_distance_km(self) -> float:
        """Retorna distancia total en kilómetros"""
        return self.total_distance_m / 1000
    
    def get_node_count(self) -> int:
        """Retorna número de nodos en la ruta"""
        return len(self.nodes)
    
    def __repr__(self):
        return (f"Route({self.nodes[0]}→{self.nodes[-1]}, "
                f"nodes={len(self.nodes)}, "
                f"dist={self.total_distance_m/1000:.2f}km, "
                f"time={self.total_time_min:.1f}min)")

# ============================================================================
# CLASE NODE (NODO)
# ============================================================================

class Node:
    """Representa un nodo (intersección) en la red de calles"""
    
    def __init__(self, node_id: int, lat: float, lon: float, 
                 hospital: Optional[Hospital] = None):
        self.node_id = node_id
        self.lat = lat
        self.lon = lon
        self.hospital = hospital
        
        # Referencias a aristas conectadas
        self.outgoing_edges: List['Edge'] = []  # Aristas que salen
        self.incoming_edges: List['Edge'] = []  # Aristas que entran
    
    def is_hospital(self) -> bool:
        """Verifica si este nodo tiene un hospital"""
        return self.hospital is not None
    
    def get_coordinates(self) -> Tuple[float, float]:
        """Retorna las coordenadas (lat, lon)"""
        return (self.lat, self.lon)
    
    def distance_to(self, other: 'Node') -> float:
        """
        Calcula distancia euclidiana a otro nodo.
        
        Args:
            other: Otro nodo
            
        Returns:
            Distancia aproximada en km
        """
        # Aproximación: 1 grado ≈ 111 km
        dlat = (self.lat - other.lat) * 111
        dlon = (self.lon - other.lon) * 111 * np.cos(np.radians(self.lat))
        return np.sqrt(dlat**2 + dlon**2)
    
    def get_neighbors(self) -> List['Node']:
        """Retorna lista de nodos vecinos (conectados por aristas salientes)"""
        return [edge.destination for edge in self.outgoing_edges]
    
    def add_outgoing_edge(self, edge: 'Edge'):
        """Añade una arista saliente"""
        if edge not in self.outgoing_edges:
            self.outgoing_edges.append(edge)
    
    def add_incoming_edge(self, edge: 'Edge'):
        """Añade una arista entrante"""
        if edge not in self.incoming_edges:
            self.incoming_edges.append(edge)
    
    def __repr__(self):
        hospital_str = f", hospital={self.hospital.name}" if self.hospital else ""
        return f"Node(id={self.node_id}, lat={self.lat:.6f}, lon={self.lon:.6f}{hospital_str})"
    
    def __hash__(self):
        return hash(self.node_id)
    
    def __eq__(self, other):
        if isinstance(other, Node):
            return self.node_id == other.node_id
        return False

# ============================================================================
# CLASE EDGE (ARISTA / CALLE)
# ============================================================================

class Edge:
    """Representa una arista (calle) entre dos nodos"""
    
    def __init__(self, 
                 origin: Node,
                 destination: Node,
                 edge_id: int,
                 length_m: float,
                 maxspeed_kmh: int,
                 lanes: int,
                 highway_type: str,
                 base_time_min: float,
                 base_risk: float,
                 surface_quality: float,
                 has_coverage: bool,
                 street_name: str = "",
                 oneway: bool = False):
        
        self.edge_id = edge_id
        self.origin = origin
        self.destination = destination
        
        # Propiedades estáticas
        self.length_m = length_m
        self.maxspeed_kmh = maxspeed_kmh
        self.lanes = lanes
        self.highway_type = highway_type
        self.base_time_min = base_time_min
        self.base_risk = base_risk
        self.surface_quality = surface_quality
        self.has_coverage = has_coverage
        self.street_name = street_name
        self.oneway = oneway
        
        # Propiedades dinámicas (cambian con tráfico)
        self.traffic_factor = 1.0  # 1.0 = normal, 2.0 = doble tiempo
        self.current_time_min = base_time_min
        self.is_blocked = False  # Si hay accidente/obra
        
        # Registrar esta arista en los nodos
        origin.add_outgoing_edge(self)
        destination.add_incoming_edge(self)
    
    def get_length_km(self) -> float:
        """Retorna longitud en kilómetros"""
        return self.length_m / 1000
    
    def update_traffic(self, traffic_factor: float):
        """
        Actualiza el factor de tráfico.
        
        Args:
            traffic_factor: Factor multiplicador (1.0=normal, 2.0=doble tiempo)
        """
        self.traffic_factor = traffic_factor
        self.current_time_min = self.base_time_min * traffic_factor
    
    def block(self):
        """Bloquea la calle (accidente, obra, etc.)"""
        self.is_blocked = True
        self.traffic_factor = float('inf')
        self.current_time_min = float('inf')
    
    def unblock(self):
        """Desbloquea la calle"""
        self.is_blocked = False
        self.traffic_factor = 1.0
        self.current_time_min = self.base_time_min
    
    def get_speed_mps(self) -> float:
        """Retorna velocidad en metros por segundo"""
        return (self.maxspeed_kmh * 1000) / 3600
    
    def get_travel_time(self, use_current_traffic: bool = True) -> float:
        """
        Calcula tiempo de viaje en minutos.
        
        Args:
            use_current_traffic: Si True, usa tráfico actual; si False, usa tiempo base
            
        Returns:
            Tiempo en minutos
        """
        if self.is_blocked:
            return float('inf')
        
        return self.current_time_min if use_current_traffic else self.base_time_min
    
    def get_risk_score(self) -> float:
        """
        Calcula score de riesgo ponderado.
        
        Returns:
            Score de 0-1 (mayor = más riesgo)
        """
        # Combinar múltiples factores
        risk = self.base_risk * 0.6  # Riesgo base 60%
        risk += (1 - self.surface_quality) * 0.3  # Calidad superficie 30%
        risk += (self.traffic_factor - 1.0) * 0.1  # Tráfico 10%
        return min(risk, 1.0)
    
    def is_highway(self) -> bool:
        """Verifica si es autopista/autovía"""
        return 'motorway' in self.highway_type or 'trunk' in self.highway_type
    
    def is_residential(self) -> bool:
        """Verifica si es calle residencial"""
        return 'residential' in self.highway_type
    
    def __repr__(self):
        blocked_str = " [BLOCKED]" if self.is_blocked else ""
        return (f"Edge(id={self.edge_id}, {self.origin.node_id}→{self.destination.node_id}, "
                f"{self.length_m:.0f}m, {self.street_name or 'Sin nombre'}{blocked_str})")
    
    def __hash__(self):
        return hash((self.origin.node_id, self.destination.node_id, self.edge_id))

# ============================================================================
# CLASE ROADNETWORK
# ============================================================================

class RoadNetwork:
    """
    Red de calles compuesta por nodos y aristas.
    """
    
    def __init__(self, graph_dir: str = 'leon_graph'):
        """
        Inicializa la red cargando datos procesados.
        
        Args:
            graph_dir: Directorio con archivos del grafo
        """
        self.graph_dir = Path(graph_dir)
        
        # Almacenamiento
        self.nodes: Dict[int, Node] = {}
        self.edges: Dict[Tuple[int, int], List[Edge]] = {}
        self.all_edges: List[Edge] = []  # Lista plana de todas las aristas
        
        # Metadata
        self.metadata: dict = None
        
        # NetworkX para algoritmos (opcional)
        self._nx_graph: Optional[nx.MultiDiGraph] = None
        
        # Cargar datos
        self._load_from_files()
        
        print(f"✅ RoadNetwork cargado: {len(self.nodes)} nodos, {len(self.all_edges)} aristas")
    
    def _load_from_files(self):
        """Carga datos desde archivos CSV"""
        nodes_path = self.graph_dir / 'nodes.csv'
        edges_path = self.graph_dir / 'edges.csv'
        metadata_path = self.graph_dir / 'metadata.json'
        
        if not nodes_path.exists():
            raise FileNotFoundError(f"No se encuentra {nodes_path}")
        
        # Cargar metadata
        with open(metadata_path, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)
        
        # Cargar nodos
        nodes_df = pd.read_csv(nodes_path)
        for _, row in nodes_df.iterrows():
            # Crear hospital si existe
            hospital = None
            if pd.notna(row['hospital_name']) and row['hospital_name'] != '':
                hospital = Hospital(
                    name=row['hospital_name'],
                    capacity=int(row['hospital_capacity']),
                    specialties=row['hospital_specialties'].split(';') if pd.notna(row['hospital_specialties']) else [],
                    has_emergency=bool(row['hospital_emergency'])
                )
            
            # Crear nodo
            node = Node(
                node_id=int(row['node_id']),
                lat=float(row['lat']),
                lon=float(row['lon']),
                hospital=hospital
            )
            
            self.nodes[node.node_id] = node
        
        # Cargar aristas
        edges_df = pd.read_csv(edges_path)
        for _, row in edges_df.iterrows():
            origin_id = int(row['origin_id'])
            dest_id = int(row['destination_id'])
            
            # Verificar que los nodos existen
            if origin_id not in self.nodes or dest_id not in self.nodes:
                continue
            
            edge = Edge(
                origin=self.nodes[origin_id],
                destination=self.nodes[dest_id],
                edge_id=int(row['edge_id']),
                length_m=float(row['length_m']),
                maxspeed_kmh=int(row['maxspeed_kmh']),
                lanes=int(row['lanes']),
                highway_type=str(row['highway_type']),
                base_time_min=float(row['base_time_min']),
                base_risk=float(row['base_risk']),
                surface_quality=float(row['surface_quality']),
                has_coverage=bool(row['has_coverage']),
                street_name=str(row['street_name']) if pd.notna(row['street_name']) else "",
                oneway=bool(row['oneway'])
            )
            
            # Almacenar arista
            key = (origin_id, dest_id)
            if key not in self.edges:
                self.edges[key] = []
            self.edges[key].append(edge)
            self.all_edges.append(edge)
    
    # ========================================================================
    # CONSULTAS DE NODOS
    # ========================================================================
    
    def get_node(self, node_id: int) -> Optional[Node]:
        """Obtiene un nodo por ID"""
        return self.nodes.get(node_id)
    
    def get_all_nodes(self) -> List[Node]:
        """Retorna todos los nodos"""
        return list(self.nodes.values())
    
    def get_node_by_coords(self, lat: float, lon: float) -> Node:
        """Encuentra el nodo más cercano a unas coordenadas"""
        min_dist = float('inf')
        nearest = None
        
        for node in self.nodes.values():
            dlat = (node.lat - lat) * 111
            dlon = (node.lon - lon) * 111 * np.cos(np.radians(lat))
            dist = np.sqrt(dlat**2 + dlon**2)
            
            if dist < min_dist:
                min_dist = dist
                nearest = node
        
        return nearest
    
    # ========================================================================
    # CONSULTAS DE ARISTAS
    # ========================================================================
    
    def get_edge(self, origin_id: int, dest_id: int) -> Optional[Edge]:
        """
        Obtiene la primera arista entre dos nodos.
        
        Args:
            origin_id: ID del nodo origen
            dest_id: ID del nodo destino
            
        Returns:
            Edge o None
        """
        edges = self.edges.get((origin_id, dest_id))
        return edges[0] if edges else None
    
    def get_all_edges_between(self, origin_id: int, dest_id: int) -> List[Edge]:
        """Obtiene todas las aristas entre dos nodos (puede haber múltiples)"""
        return self.edges.get((origin_id, dest_id), [])
    
    def get_all_edges(self) -> List[Edge]:
        """Retorna todas las aristas"""
        return self.all_edges
    
    # ========================================================================
    # CONSULTAS DE HOSPITALES
    # ========================================================================
    
    def get_hospitals(self) -> List[Node]:
        """Retorna lista de nodos que son hospitales"""
        return [node for node in self.nodes.values() if node.is_hospital()]
    
    def get_nearest_hospital(self, node: Node) -> Optional[Node]:
        """Encuentra el hospital más cercano a un nodo"""
        hospitals = self.get_hospitals()
        if not hospitals:
            return None
        
        min_dist = float('inf')
        nearest = None
        
        for hospital in hospitals:
            dist = node.distance_to(hospital)
            if dist < min_dist:
                min_dist = dist
                nearest = hospital
        
        return nearest
    
    # ========================================================================
    # ACTUALIZACIÓN DE TRÁFICO
    # ========================================================================
    
    def update_edge_traffic(self, origin_id: int, dest_id: int, traffic_factor: float):
        """Actualiza el tráfico de una arista"""
        edges = self.get_all_edges_between(origin_id, dest_id)
        for edge in edges:
            edge.update_traffic(traffic_factor)
    
    def update_all_traffic(self, traffic_factors: Dict[Tuple[int, int], float]):
        """
        Actualiza el tráfico de múltiples aristas.
        
        Args:
            traffic_factors: Diccionario {(origin_id, dest_id): factor}
        """
        for (origin_id, dest_id), factor in traffic_factors.items():
            self.update_edge_traffic(origin_id, dest_id, factor)
    
    def reset_all_traffic(self):
        """Resetea el tráfico de todas las aristas a valores base"""
        for edge in self.all_edges:
            edge.update_traffic(1.0)
    
    # ========================================================================
    # UTILIDADES DE RUTAS
    # ========================================================================
    
    def print_route_details(self, route: Route):
        """Imprime detalles de una ruta"""
        print("\n" + "="*80)
        print(f"📍 RUTA: Nodo {route.nodes[0]} → Nodo {route.nodes[-1]}")
        print("="*80)
        print(f"   📏 Distancia total: {route.get_total_distance_km():.2f} km")
        print(f"   ⏱️  Tiempo estimado: {route.total_time_min:.1f} min")
        print(f"   ⚠️  Riesgo promedio: {route.total_risk:.3f}")
        print(f"   🚦 Factor tráfico promedio: {route.avg_traffic_factor:.2f}x")
        print(f"   🔢 Número de nodos: {route.get_node_count()}")
        print(f"\n   🛣️  Calles en la ruta:")
        
        for i, edge in enumerate(route.edges, 1):
            name = edge.street_name if edge.street_name else "Sin nombre"
            print(f"      {i}. {name} ({edge.length_m:.0f}m, "
                  f"{edge.current_time_min:.1f}min, "
                  f"tráfico: {edge.traffic_factor:.1f}x)")
        
        print("="*80)
    
    # ========================================================================
    # UTILIDADES
    # ========================================================================
    
    def get_stats(self) -> dict:
        """Retorna estadísticas de la red"""
        return {
            'total_nodes': len(self.nodes),
            'total_edges': len(self.all_edges),
            'total_hospitals': len(self.get_hospitals()),
            'avg_edges_per_node': len(self.all_edges) / len(self.nodes) if self.nodes else 0,
            'city': self.metadata.get('city', 'Unknown')
        }
    
    def __repr__(self):
        return (f"RoadNetwork(nodes={len(self.nodes)}, "
                f"edges={len(self.all_edges)}, "
                f"hospitals={len(self.get_hospitals())})")