
class model_ambulance:
    """
    Clase encargada de almacenar la información estática y de identificación de la ambulancia.
    Esta capa NO gestiona telemetría ni datos dinámicos. Sirve de unión al resto de componentes del gemelo digital.
    """

    def __init__(
        self,
        id_unico: str,
        matricula: str,
        marca: str,
        modelo: str,
        año: int,
        tipo: str,
        hospital_base: str,
        numero_bastidor: str,
        equipamiento: list = None,
        metadata_extra: dict = None
    ):
        self._id_unico = id_unico
        self._matricula = matricula
        self._marca = marca
        self._modelo = modelo
        self._año = año
        self._tipo = tipo
        self._hospital_base = hospital_base
        self._numero_bastidor = numero_bastidor
        self._equipamiento = equipamiento if equipamiento is not None else []
        self._metadata_extra = metadata_extra if metadata_extra is not None else {}

        self._capa_fisica = None
        self._capa_persistencia = None
        self._capa_servicios = None
        self._capa_analisis = None
        self._capa_visualizacion = None
        self._capa_comunicacion = None

    @property
    def id_unico(self): return self._id_unico
    @id_unico.setter
    def id_unico(self, value): self._id_unico = value

    @property
    def matricula(self): return self._matricula
    @matricula.setter
    def matricula(self, value): self._matricula = value

    @property
    def marca(self): return self._marca
    @marca.setter
    def marca(self, value): self._marca = value

    @property
    def modelo(self): return self._modelo
    @modelo.setter
    def modelo(self, value): self._modelo = value

    @property
    def año(self): return self._año
    @año.setter
    def año(self, value): self._año = value

    @property
    def tipo(self): return self._tipo
    @tipo.setter
    def tipo(self, value): self._tipo = value

    @property
    def hospital_base(self): return self._hospital_base
    @hospital_base.setter
    def hospital_base(self, value): self._hospital_base = value

    @property
    def numero_bastidor(self): return self._numero_bastidor
    @numero_bastidor.setter
    def numero_bastidor(self, value): self._numero_bastidor = value

    @property
    def equipamiento(self): return self._equipamiento
    @equipamiento.setter
    def equipamiento(self, value): self._equipamiento = value

    @property
    def metadata_extra(self): return self._metadata_extra
    @metadata_extra.setter
    def metadata_extra(self, value): self._metadata_extra = value

    @property
    def capa_fisica(self): return self._capa_fisica
    @capa_fisica.setter
    def capa_fisica(self, value): self._capa_fisica = value

    @property
    def capa_persistencia(self): return self._capa_persistencia
    @capa_persistencia.setter
    def capa_persistencia(self, value): self._capa_persistencia = value

    @property
    def capa_servicios(self): return self._capa_servicios
    @capa_servicios.setter
    def capa_servicios(self, value): self._capa_servicios = value

    @property
    def capa_analisis(self): return self._capa_analisis
    @capa_analisis.setter
    def capa_analisis(self, value): self._capa_analisis = value

    @property
    def capa_visualizacion(self): return self._capa_visualizacion
    @capa_visualizacion.setter
    def capa_visualizacion(self, value): self._capa_visualizacion = value

    @property
    def capa_comunicacion(self): return self._capa_comunicacion
    @capa_comunicacion.setter
    def capa_comunicacion(self, value): self._capa_comunicacion = value

    def __str__(self):
        return f"Ambulancia[{self.id_unico}]: {self.matricula}"

    def to_detailed_string(self):
        return (f"--- Detalle Ambulancia ---\n"
                f"ID: {self.id_unico}\nMatrícula: {self.matricula}\n"
                f"Vehículo: {self.marca} {self.modelo} ({self.año})\n"
                f"Tipo: {self.tipo}\nHospital: {self.hospital_base}\n"
                f"Bastidor: {self.numero_bastidor}\nEquipamiento: {self.equipamiento}\n"
                f"Metadata: {self.metadata_extra}")
