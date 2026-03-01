import math
import random


def seleccionar_nodos_paciente(road, n=30):
    """
    Selecciona n nodos distribuidos uniformemente por cuadrícula lat/lon.
    Excluye nodos de hospitales.
    Devuelve List[int] con los node_ids seleccionados.
    """
    hospital_ids = {node.node_id for node in road.get_hospitals()}
    candidatos = [node for node_id, node in road.nodes.items() if node_id not in hospital_ids]

    lats = [nd.lat for nd in candidatos]
    lons = [nd.lon for nd in candidatos]
    lat_min, lat_max = min(lats), max(lats)
    lon_min, lon_max = min(lons), max(lons)

    filas = math.ceil(math.sqrt(n))
    cols = math.ceil(n / filas)

    seleccionados = []
    for i in range(filas):
        for j in range(cols):
            lat_lo = lat_min + i * (lat_max - lat_min) / filas
            lat_hi = lat_min + (i + 1) * (lat_max - lat_min) / filas
            lon_lo = lon_min + j * (lon_max - lon_min) / cols
            lon_hi = lon_min + (j + 1) * (lon_max - lon_min) / cols
            celda = [nd for nd in candidatos if lat_lo <= nd.lat < lat_hi and lon_lo <= nd.lon < lon_hi]
            if celda:
                elegido = random.choice(celda)
                seleccionados.append(elegido.node_id)
            if len(seleccionados) >= n:
                break
        if len(seleccionados) >= n:
            break

    # Rellenar si faltan
    while len(seleccionados) < n and candidatos:
        extra = random.choice(candidatos)
        if extra.node_id not in seleccionados:
            seleccionados.append(extra.node_id)

    return seleccionados[:n]
