from dataclasses import dataclass, field
from typing import List, Optional, Dict, TYPE_CHECKING

from Model.Map.RoadNetwork import RoadNetwork, Route
from Model.Prediccion.route_calculator.base_route_strategy import BaseRouteStrategy
from Model.Prediccion.route_calculator.dijkstra_strategy import DijkstraRouteStrategy


@dataclass
class ScoredRoute:
    """
    Ruta calculada junto con su puntuación y metadatos de evaluación.

    Atributos:
        route: Objeto Route con la secuencia de nodos y aristas.
        score: Puntuación global de 0.0 (peor) a 1.0 (mejor aptitud).
        label: Etiqueta descriptiva ('Más rápida', 'Más segura', 'Más corta').
        breakdown: Desglose de métricas usadas para calcular el score.
        puede_tratar: Indica si el hospital destino puede tratar la afección.
                      None si no se proporcionó afección para filtrar.
    """
    route: Route
    score: float
    label: str
    breakdown: dict
    puede_tratar: Optional[bool] = field(default=None)

    def __repr__(self):
        return (f"ScoredRoute(label='{self.label}', score={self.score:.4f}, "
                f"tiempo={self.breakdown.get('tiempo', 0):.1f}min)")


class AnalisisLayer:
    """
    Orquestador principal de la Capa de Predicción y Análisis.

    Consume un grafo de red vial (RoadNetwork) y una estrategia de cálculo
    de rutas inyectada (patrón Strategy) para exponer servicios de análisis
    de alto nivel.

    Atributos:
        road: Red de calles sobre la que operar.
        estrategia: Algoritmo de cálculo de rutas a usar.
    """

    def __init__(self,
                 road: RoadNetwork,
                 estrategia: Optional[BaseRouteStrategy] = None):
        """
        Inicializa la capa de análisis.

        Args:
            road: Instancia de RoadNetwork con los datos del grafo.
            estrategia: Estrategia de cálculo de rutas. Si no se indica,
                        se usa DijkstraRouteStrategy por defecto.
        """
        self.road = road
        self.estrategia: BaseRouteStrategy = estrategia or DijkstraRouteStrategy()

    def set_estrategia(self, estrategia: BaseRouteStrategy) -> None:
        """
        Permite cambiar la estrategia de rutas en tiempo de ejecución.

        Args:
            estrategia: Nueva instancia de BaseRouteStrategy a usar.
        """
        self.estrategia = estrategia

    # ------------------------------------------------------------------ #
    # Métodos públicos de análisis de rutas                                #
    # ------------------------------------------------------------------ #

    def calcular_rutas(self, origin_id: int, dest_id: int) -> List[ScoredRoute]:
        """
        Calcula y puntúa rutas entre dos nodos usando la estrategia activa.

        Args:
            origin_id: ID del nodo origen.
            dest_id: ID del nodo destino.

        Returns:
            Lista de ScoredRoute ordenada por score descendente.
        """
        return self.estrategia.calculate(self.road, origin_id, dest_id)

    def recomendar_mejor_ruta(self, origin_id: int, dest_id: int) -> Optional[ScoredRoute]:
        """
        Devuelve únicamente la ruta con mayor score entre dos nodos.

        Args:
            origin_id: ID del nodo origen.
            dest_id: ID del nodo destino.

        Returns:
            ScoredRoute con mayor score, o None si no hay ruta posible.
        """
        rutas = self.calcular_rutas(origin_id, dest_id)
        return rutas[0] if rutas else None

    def recomendar_hospital(
        self,
        origin_id: int,
        afeccion: Optional[str] = None,
        afecciones_db: Optional[Dict] = None,
    ) -> List[ScoredRoute]:
        """
        Recomienda hospitales usando un sistema de torneo por etapas:

        ETAPA 1 — Filtro eliminatorio (si se proporciona afeccion):
            Solo pasan los hospitales que pueden tratar la afección del paciente.
            Los que no puedan tratarla quedan ELIMINADOS del ranking principal
            y se añaden al final marcados con puede_tratar=False.

        ETAPA 2 — Score combinado entre los hospitales que pasan el filtro:
            Se calcula un score_hospital que combina:
              · Camas disponibles      (peso 0.45) — prioridad alta
              · Urgencias 24h          (peso 0.25) — prioridad media
              · Score de ruta          (peso 0.30) — prioridad baja

            La normalización de camas se hace respecto al máximo de la lista
            filtrada, de modo que el hospital con más camas libres obtiene 1.0.

        RESULTADO:
            Lista de ScoredRoute donde:
              - Los hospitales aptos aparecen primero, ordenados por score_hospital.
              - Los no aptos aparecen al final, ordenados por score de ruta,
                marcados con puede_tratar=False.

        Args:
            origin_id: ID del nodo desde el que parte la ambulancia.
            afeccion: Nombre de la afección del paciente (clave de afecciones_db).
            afecciones_db: Dict con la BD de afecciones (ver afecciones_db.py).

        Returns:
            Lista de ScoredRoute ordenada según las etapas descritas.
        """
        hospitales = self.road.get_hospitals()

        # ── Paso 1: calcular la mejor ruta a cada hospital ──────────────
        candidatos = []   # (ScoredRoute, hospital_obj)
        for hospital_node in hospitales:
            if hospital_node.node_id == origin_id:
                continue
            mejor = self.recomendar_mejor_ruta(origin_id, hospital_node.node_id)
            if mejor:
                candidatos.append((mejor, hospital_node.hospital))

        if not candidatos:
            return []

        # ── Paso 2: determinar si cada hospital puede tratar la afección ─
        required_specs: List[str] = []
        if afeccion and afecciones_db:
            required_specs = afecciones_db.get(afeccion, {}).get('specialties_required', [])

        def _puede_tratar(hospital) -> bool:
            if not required_specs:
                return True   # sin filtro, todos pasan
            return any(hospital.has_specialty(sp) for sp in required_specs)

        aptos = []
        no_aptos = []
        for scored, hospital in candidatos:
            if _puede_tratar(hospital):
                aptos.append((scored, hospital))
            else:
                scored.puede_tratar = False
                no_aptos.append((scored, hospital))

        # ── Paso 3: score combinado sólo entre los aptos ────────────────
        #
        # score_hospital = 0.45 * norm_camas
        #                + 0.25 * urgencias_24h
        #                + 0.30 * score_ruta
        #
        if aptos:
            max_camas = max(h.get_available_beds() for _, h in aptos) or 1

            for scored, hospital in aptos:
                norm_camas    = hospital.get_available_beds() / max_camas
                bonus_urgencias = 1.0 if hospital.has_emergency else 0.0
                score_ruta    = scored.score   # ya está en [0, 1]

                score_hospital = (
                    0.45 * norm_camas
                    + 0.25 * bonus_urgencias
                    + 0.30 * score_ruta
                )

                # Guardamos el score combinado y el desglose en el objeto
                scored.breakdown['score_hospital'] = round(score_hospital, 4)
                scored.breakdown['camas_libres']   = hospital.get_available_beds()
                scored.breakdown['urgencias_24h']  = hospital.has_emergency
                scored.score = score_hospital
                scored.puede_tratar = True

            aptos.sort(key=lambda t: t[0].score, reverse=True)

        # ── Paso 4: los no aptos van al final ordenados por score de ruta ─
        no_aptos.sort(key=lambda t: t[0].score, reverse=True)

        # ── Resultado final ──────────────────────────────────────────────
        return [s for s, _ in aptos] + [s for s, _ in no_aptos]

    # ------------------------------------------------------------------ #
    # Huecos para futuros módulos de IA                                    #
    # ------------------------------------------------------------------ #

    # TODO: predecir_fallo_mecanico(self, telemetria: dict) -> dict:
    #   Módulo de predicción de fallos mecánicos basado en datos del motor.
    #   Recibirá la telemetría actual y devolverá probabilidad y tipo de fallo.

    # TODO: detectar_anomalia_clinica(self, signos_vitales: dict) -> dict:
    #   Módulo de detección de anomalías clínicas del paciente.
    #   Analizará FC, SpO2, temperatura, etc. y alertará sobre eventos críticos.