import math
import random


def seleccionar_nodos_paciente(road, n=30):
    """
    Selecciona n nodos distribuidos uniformemente por el mapa usando
    una cuadrícula lat/lon.

    Divide el bbox de los nodos en una cuadrícula de ceil(sqrt(n)) x ceil(sqrt(n))
    celdas y selecciona 1 nodo aleatorio de cada celda (si hay nodos en ella).
    Excluye los nodos de hospitales.
    """
    hospital_ids = {node.node_id for node in road.get_hospitals()}
    candidatos = [
        node for node_id, node in road.nodes.items()
        if node_id not in hospital_ids
    ]

    if not candidatos:
        return []

    lats = [node.lat for node in candidatos]
    lons = [node.lon for node in candidatos]
    lat_min, lat_max = min(lats), max(lats)
    lon_min, lon_max = min(lons), max(lons)

    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(math.sqrt(n))

    lat_step = (lat_max - lat_min) / rows if lat_max != lat_min else 1
    lon_step = (lon_max - lon_min) / cols if lon_max != lon_min else 1

    grid = {}
    for node in candidatos:
        r = min(int((node.lat - lat_min) / lat_step), rows - 1)
        c = min(int((node.lon - lon_min) / lon_step), cols - 1)
        grid.setdefault((r, c), []).append(node.node_id)

    seleccionados = []
    for cell_nodes in grid.values():
        if len(seleccionados) >= n:
            break
        seleccionados.append(random.choice(cell_nodes))

    # Rellenar con nodos aleatorios si hay celdas vacías
    if len(seleccionados) < n:
        todos_ids = [node.node_id for node in candidatos]
        ya_seleccionados = set(seleccionados)
        restantes = [nid for nid in todos_ids if nid not in ya_seleccionados]
        random.shuffle(restantes)
        seleccionados.extend(restantes[:n - len(seleccionados)])

    return seleccionados[:n]
